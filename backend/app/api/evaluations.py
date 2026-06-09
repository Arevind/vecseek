from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import EvalCase, EvalProfile, EvalProvider, EvalRun, EvalRunType, EvalTriggerType, Folder
from app.schemas import EvalCaseRequest, EvalCaseResponse, EvalProfileResponse, EvalProfileUpdateRequest, EvalRunArtifactResponse, EvalRunDetailResponse, EvalRunItemResponse, EvalRunStartRequest, EvalRunSummaryResponse, OllamaModelsListResponse
from app.services.eval_generation import list_ollama_models
from app.services.eval_queue import eval_queue
from app.services.eval_service import create_eval_run, get_or_create_eval_profile, resolve_folder
from app.utils.errors import bad_request, not_found

router = APIRouter(tags=["evaluations"])


def _resolve_run(db: Session, folder: Folder, run_id: str) -> EvalRun:
    run = db.query(EvalRun).filter(EvalRun.folder_id == folder.id, EvalRun.id == run_id).first()
    if not run:
        raise not_found("Evaluation run not found.")
    return run


@router.get("/eval/providers/ollama/models", response_model=OllamaModelsListResponse)
async def list_ollama_models_endpoint() -> OllamaModelsListResponse:
    return OllamaModelsListResponse(models=await list_ollama_models())


@router.get("/folders/{folder_name}/evaluations/profile", response_model=EvalProfileResponse)
def get_eval_profile(folder_name: str, db: Session = Depends(get_db)) -> EvalProfileResponse:
    folder = resolve_folder(db, folder_name)
    profile = get_or_create_eval_profile(db, folder)
    return EvalProfileResponse.model_validate(profile)


@router.patch("/folders/{folder_name}/evaluations/profile", response_model=EvalProfileResponse)
def update_eval_profile(
    folder_name: str,
    payload: EvalProfileUpdateRequest,
    db: Session = Depends(get_db),
) -> EvalProfileResponse:
    folder = resolve_folder(db, folder_name)
    if payload.provider.value == "openai" and payload.auto_run_enabled:
        raise bad_request("Auto-run is only available for Ollama-backed evaluations because OpenAI keys are stored in the browser only.")
    profile = get_or_create_eval_profile(db, folder)
    profile.provider = payload.provider
    profile.model_name = payload.model_name
    profile.auto_run_enabled = payload.auto_run_enabled
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return EvalProfileResponse.model_validate(profile)


@router.get("/folders/{folder_name}/evaluations/cases", response_model=list[EvalCaseResponse])
def list_eval_cases(folder_name: str, db: Session = Depends(get_db)) -> list[EvalCaseResponse]:
    folder = resolve_folder(db, folder_name)
    cases = db.query(EvalCase).filter(EvalCase.folder_id == folder.id).order_by(EvalCase.created_at.desc()).all()
    return [EvalCaseResponse.model_validate(item) for item in cases]


@router.post("/folders/{folder_name}/evaluations/cases", response_model=EvalCaseResponse)
def create_eval_case(folder_name: str, payload: EvalCaseRequest, db: Session = Depends(get_db)) -> EvalCaseResponse:
    folder = resolve_folder(db, folder_name)
    case = EvalCase(folder_id=folder.id, **payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return EvalCaseResponse.model_validate(case)


@router.patch("/folders/{folder_name}/evaluations/cases/{case_id}", response_model=EvalCaseResponse)
def update_eval_case(
    folder_name: str,
    case_id: str,
    payload: EvalCaseRequest,
    db: Session = Depends(get_db),
) -> EvalCaseResponse:
    folder = resolve_folder(db, folder_name)
    case = db.query(EvalCase).filter(EvalCase.folder_id == folder.id, EvalCase.id == case_id).first()
    if not case:
        raise not_found("Evaluation case not found.")
    for key, value in payload.model_dump().items():
        setattr(case, key, value)
    db.add(case)
    db.commit()
    db.refresh(case)
    return EvalCaseResponse.model_validate(case)


@router.delete("/folders/{folder_name}/evaluations/cases/{case_id}")
def delete_eval_case(folder_name: str, case_id: str, db: Session = Depends(get_db)) -> dict:
    folder = resolve_folder(db, folder_name)
    case = db.query(EvalCase).filter(EvalCase.folder_id == folder.id, EvalCase.id == case_id).first()
    if not case:
        raise not_found("Evaluation case not found.")
    db.delete(case)
    db.commit()
    return {"status": "success", "message": "Evaluation case deleted successfully."}


@router.get("/folders/{folder_name}/evaluations/runs", response_model=list[EvalRunSummaryResponse])
def list_eval_runs(folder_name: str, db: Session = Depends(get_db)) -> list[EvalRunSummaryResponse]:
    folder = resolve_folder(db, folder_name)
    runs = db.query(EvalRun).filter(EvalRun.folder_id == folder.id).order_by(EvalRun.started_at.desc()).all()
    return [EvalRunSummaryResponse.model_validate(run) for run in runs]


@router.post("/folders/{folder_name}/evaluations/runs", response_model=EvalRunSummaryResponse)
def start_eval_run(folder_name: str, payload: EvalRunStartRequest, db: Session = Depends(get_db)) -> EvalRunSummaryResponse:
    folder = resolve_folder(db, folder_name)
    profile = get_or_create_eval_profile(db, folder)
    provider = payload.provider or profile.provider
    model_name = (payload.model_name or profile.model_name).strip()
    if not model_name:
        raise bad_request("A model_name is required to run evaluations.")
    if provider == EvalProvider.OPENAI and payload.run_type in {EvalRunType.FULL, EvalRunType.ANSWER, EvalRunType.REDTEAM} and not payload.openai_api_key:
        raise bad_request("An OpenAI API key is required for answer or red-team evaluation runs.")
    run = create_eval_run(
        db=db,
        folder=folder,
        run_type=payload.run_type,
        trigger_type=EvalTriggerType.MANUAL,
        provider=provider,
        model_name=model_name,
    )
    eval_queue.enqueue(run.id, openai_api_key=payload.openai_api_key)
    db.refresh(run)
    return EvalRunSummaryResponse.model_validate(run)


@router.get("/folders/{folder_name}/evaluations/runs/{run_id}", response_model=EvalRunDetailResponse)
def get_eval_run(folder_name: str, run_id: str, db: Session = Depends(get_db)) -> EvalRunDetailResponse:
    folder = resolve_folder(db, folder_name)
    run = _resolve_run(db, folder, run_id)
    db.refresh(run)
    return EvalRunDetailResponse(
        **EvalRunSummaryResponse.model_validate(run).model_dump(),
        items=[EvalRunItemResponse.model_validate(item) for item in run.run_items],
        artifacts=[EvalRunArtifactResponse.model_validate(artifact) for artifact in run.artifacts],
    )


@router.get("/folders/{folder_name}/evaluations/runs/{run_id}/status", response_model=EvalRunSummaryResponse)
def get_eval_run_status(folder_name: str, run_id: str, db: Session = Depends(get_db)) -> EvalRunSummaryResponse:
    folder = resolve_folder(db, folder_name)
    run = _resolve_run(db, folder, run_id)
    return EvalRunSummaryResponse.model_validate(run)
