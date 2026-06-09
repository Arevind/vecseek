from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from statistics import mean
from time import perf_counter

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    EvalCase,
    EvalCaseType,
    EvalProfile,
    EvalProvider,
    EvalRun,
    EvalRunArtifact,
    EvalRunItem,
    EvalRunStatus,
    EvalRunType,
    EvalTriggerType,
    Folder,
)
from app.schemas import RetrievalResponse
from app.services.eval_generation import generate_eval_answer
from app.services.eval_metrics import answer_case_score, redteam_case_score, retrieval_case_score
from app.services.retrieval_service import retrieve
from app.services.runtime_metrics import metrics
from app.utils.errors import bad_request, not_found
from app.utils.slugs import normalize_name


def get_or_create_eval_profile(db: Session, folder: Folder) -> EvalProfile:
    profile = db.query(EvalProfile).filter(EvalProfile.folder_id == folder.id).first()
    if profile:
        return profile
    profile = EvalProfile(folder_id=folder.id, provider=EvalProvider.OLLAMA, model_name="", auto_run_enabled=False)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def resolve_folder(db: Session, folder_name: str) -> Folder:
    folder = db.query(Folder).filter(Folder.normalized_name == normalize_name(folder_name)).first()
    if not folder:
        raise not_found("Folder not found.")
    return folder


def _case_matches_run(case: EvalCase, run_type: EvalRunType) -> bool:
    if case.case_type == EvalCaseType.ALL:
        return True
    mapping = {
        EvalCaseType.RETRIEVAL: EvalRunType.RETRIEVAL,
        EvalCaseType.ANSWER: EvalRunType.ANSWER,
        EvalCaseType.REDTEAM: EvalRunType.REDTEAM,
    }
    return mapping.get(case.case_type) == run_type or run_type == EvalRunType.FULL


def create_eval_run(
    db: Session,
    folder: Folder,
    run_type: EvalRunType,
    trigger_type: EvalTriggerType,
    provider: EvalProvider,
    model_name: str,
) -> EvalRun:
    previous = (
        db.query(EvalRun)
        .filter(EvalRun.folder_id == folder.id)
        .order_by(EvalRun.started_at.desc())
        .first()
    )
    profile = get_or_create_eval_profile(db, folder)
    run = EvalRun(
        folder_id=folder.id,
        profile_id=profile.id,
        previous_run_id=previous.id if previous else None,
        run_type=run_type,
        trigger_type=trigger_type,
        status=EvalRunStatus.PENDING,
        provider=provider,
        model_name=model_name,
        summary_metrics={},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _retrieval_payload(response: RetrievalResponse) -> list[dict]:
    return [{"content": item.content, **item.metadata} for item in response.results]


def _avg(values: list[float]) -> float:
    return round(mean(values), 4) if values else 0.0


async def run_eval_job(db: Session, run_id: str, openai_api_key: str | None = None) -> None:
    settings = get_settings()
    started = perf_counter()
    run = db.query(EvalRun).filter(EvalRun.id == run_id).first()
    if not run:
        return
    folder = db.query(Folder).filter(Folder.id == run.folder_id).first()
    if not folder:
        run.status = EvalRunStatus.FAILED
        run.error_message = "Folder not found."
        db.add(run)
        db.commit()
        return

    run.status = EvalRunStatus.RUNNING
    db.add(run)
    db.commit()

    try:
        enabled_cases = [
            case
            for case in db.query(EvalCase).filter(EvalCase.folder_id == folder.id, EvalCase.enabled.is_(True)).all()
            if _case_matches_run(case, run.run_type)
        ]
        if not enabled_cases:
            raise bad_request("No enabled evaluation cases matched this run.")

        retrieval_scores: list[float] = []
        answer_scores: list[float] = []
        redteam_scores: list[float] = []
        artifact_lines: list[str] = []

        for case in enabled_cases:
            retrieval_response = retrieve(db, folder.display_name, case.question, 5, settings.max_top_k, settings.retrieval_timeout_seconds)
            retrieval_results = _retrieval_payload(retrieval_response)
            result_sources = [str(item.get("source_file", "")) for item in retrieval_results]
            context_text = "\n\n".join(item.get("content", "") for item in retrieval_results)

            if run.run_type in {EvalRunType.FULL, EvalRunType.RETRIEVAL} and case.case_type in {EvalCaseType.ALL, EvalCaseType.RETRIEVAL}:
                retrieval_metrics = retrieval_case_score(case.expected_source_files, result_sources, retrieval_response.top_k)
                retrieval_scores.append(float(retrieval_metrics["score"]))
                db.add(
                    EvalRunItem(
                        run_id=run.id,
                        case_id=case.id,
                        eval_type=EvalRunType.RETRIEVAL,
                        score=float(retrieval_metrics["score"]),
                        passed=bool(retrieval_metrics["hit_presence"] > 0 and retrieval_metrics["source_match_correctness"] > 0),
                        details={
                            "question": case.question,
                            "expected_source_files": case.expected_source_files,
                            "retrieved_source_files": result_sources,
                            **retrieval_metrics,
                        },
                    )
                )

            generated_answer = None
            if run.run_type in {EvalRunType.FULL, EvalRunType.ANSWER, EvalRunType.REDTEAM} and case.case_type in {EvalCaseType.ALL, EvalCaseType.ANSWER, EvalCaseType.REDTEAM}:
                generated_answer = await generate_eval_answer(
                    provider=run.provider,
                    model_name=run.model_name,
                    question=case.question,
                    retrieval_results=retrieval_results,
                    openai_api_key=openai_api_key,
                )

            if generated_answer and run.run_type in {EvalRunType.FULL, EvalRunType.ANSWER} and case.case_type in {EvalCaseType.ALL, EvalCaseType.ANSWER}:
                answer_metrics = answer_case_score(
                    question=case.question,
                    reference_answer=case.reference_answer,
                    expected_points=case.expected_answer_points,
                    generated_answer=generated_answer,
                    retrieved_context=context_text,
                )
                answer_scores.append(float(answer_metrics["score"]))
                db.add(
                    EvalRunItem(
                        run_id=run.id,
                        case_id=case.id,
                        eval_type=EvalRunType.ANSWER,
                        score=float(answer_metrics["score"]),
                        passed=bool(answer_metrics["score"] >= 0.45),
                        details={
                            "question": case.question,
                            "generated_answer": generated_answer,
                            "reference_answer": case.reference_answer,
                            "expected_answer_points": case.expected_answer_points,
                            **answer_metrics,
                        },
                    )
                )

            if generated_answer and run.run_type in {EvalRunType.FULL, EvalRunType.REDTEAM} and case.case_type in {EvalCaseType.ALL, EvalCaseType.REDTEAM}:
                redteam_metrics = redteam_case_score(case.question, generated_answer, result_sources)
                redteam_scores.append(float(redteam_metrics["score"]))
                artifact_lines.append(f"{case.name}: {redteam_metrics}")
                db.add(
                    EvalRunItem(
                        run_id=run.id,
                        case_id=case.id,
                        eval_type=EvalRunType.REDTEAM,
                        score=float(redteam_metrics["score"]),
                        passed=bool(redteam_metrics["passed"]),
                        details={
                            "question": case.question,
                            "generated_answer": generated_answer,
                            "retrieved_source_files": result_sources,
                            **redteam_metrics,
                        },
                    )
                )

        if artifact_lines:
            db.add(
                EvalRunArtifact(
                    run_id=run.id,
                    artifact_type="promptfoo-report",
                    name="promptfoo-fallback-report.txt",
                    content="\n".join(artifact_lines),
                )
            )

        run.status = EvalRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)
        run.summary_metrics = {
            "retrieval_average": _avg(retrieval_scores),
            "answer_average": _avg(answer_scores),
            "redteam_average": _avg(redteam_scores),
            "overall_average": _avg(retrieval_scores + answer_scores + redteam_scores),
            "cases_evaluated": len(enabled_cases),
        }
        db.add(run)
        db.commit()
        metrics.record_eval_time(perf_counter() - started)
    except Exception as exc:
        run.status = EvalRunStatus.FAILED
        run.error_message = exc.detail if isinstance(exc, HTTPException) else str(exc)
        run.completed_at = datetime.now(timezone.utc)
        db.add(run)
        db.commit()
        raise


def run_eval_job_sync(db: Session, run_id: str, openai_api_key: str | None = None) -> None:
    asyncio.run(run_eval_job(db, run_id, openai_api_key=openai_api_key))
