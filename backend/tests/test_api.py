import os
import tempfile
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

temp_dir = tempfile.mkdtemp(prefix="vecseek-tests-")
os.environ["UPLOAD_DIR"] = os.path.join(temp_dir, "uploads")
os.environ["QDRANT_DIR"] = os.path.join(temp_dir, "qdrant")
os.environ["SQLITE_PATH"] = os.path.join(temp_dir, "knowledgebase.db")

from app.config import get_settings as _settings_factory  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import EvalProfile, EvalProvider, EvalRun, EvalRunStatus, EvalRunType, EvalTriggerType, Folder, FolderStatus  # noqa: E402

_settings_factory.cache_clear()

client = TestClient(app)


def _settings_payload(**overrides):
    payload = {
        "default_top_k": 5,
        "chunk_size": 1400,
        "chunk_overlap": 250,
        "vector_candidate_limit": 32,
        "retrieval_concurrency_limit": 12,
        "indexing_worker_concurrency": 2,
        "hybrid_retrieval_enabled": True,
        "reranker_enabled": True,
    }
    payload.update(overrides)
    return payload


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_diagnostics() -> None:
    response = client.get("/health/diagnostics")
    assert response.status_code == 200
    assert "runtime_metrics" in response.json()


def test_create_folder_and_reject_duplicate() -> None:
    response = client.post("/folders", json={"folder_name": "Aadhaar SOP Docs"})
    assert response.status_code == 200
    duplicate = client.post("/folders", json={"folder_name": "aadhaar sop docs"})
    assert duplicate.status_code == 409


def test_settings_validation() -> None:
    response = client.patch("/settings", json=_settings_payload(default_top_k=999))
    assert response.status_code == 400


def test_settings_reject_overlap_greater_than_size() -> None:
    response = client.patch("/settings", json=_settings_payload(chunk_size=400, chunk_overlap=400))
    assert response.status_code == 400


def test_settings_reject_candidate_limit_below_top_k() -> None:
    response = client.patch("/settings", json=_settings_payload(default_top_k=10, vector_candidate_limit=5))
    assert response.status_code == 400


def test_folder_creation_no_longer_requires_api_key() -> None:
    response = client.post("/folders", json={"folder_name": "No Key"})
    assert response.status_code == 200


def test_upload_rejects_unsupported_file() -> None:
    client.post("/folders", json={"folder_name": "Uploads"})
    response = client.post(
        "/folders/Uploads/upload",
        files=[("files", ("malware.exe", b"binary", "application/octet-stream"))],
    )
    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == "error"


def test_retrieve_merges_dense_and_keyword_results(monkeypatch) -> None:
    client.post("/folders", json={"folder_name": "Hybrid Docs"})
    with SessionLocal() as db:
        folder = db.query(Folder).filter(Folder.normalized_name == "hybrid docs").first()
        assert folder is not None
        folder.status = FolderStatus.INDEXED
        db.add(folder)
        db.commit()

    from app.services import retrieval_service

    monkeypatch.setattr(retrieval_service, "embed_texts", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retrieval_service,
        "search_collection",
        lambda collection_name, query_vector, limit: [
            SimpleNamespace(
                id="dense-1",
                score=0.88,
                payload={
                    "chunk_id": "dense-1",
                    "source_file": "guide.txt",
                    "file_type": "txt",
                    "content_type": "text",
                    "page_number": -1,
                    "table_index": -1,
                    "row_index": -1,
                    "chunk_index": 0,
                    "content": "Pay10 helps merchants accept payments online with easy onboarding.",
                },
            )
        ],
    )
    monkeypatch.setattr(
        retrieval_service,
        "search_keyword_chunks",
        lambda db, folder_id, query, limit: [
            {
                "id": "keyword-1",
                "source_file": "faq.txt",
                "file_type": "txt",
                "content_type": "text",
                "page_number": -1,
                "table_index": -1,
                "row_index": -1,
                "chunk_index": 0,
                "file_hash": "abc",
                "content": "What is Pay10? Pay10 is a payment gateway for growing businesses.",
                "bm25_score": -2.3,
            }
        ],
    )

    response = client.post(
        "/retrieve",
        json={"folder_name": "Hybrid Docs", "query": "What is Pay10?", "top_k": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    assert any("keyword overlap" in item["metadata"].get("explanation", "") for item in body["results"])


def test_eval_profile_create_and_update() -> None:
    client.post("/folders", json={"folder_name": "Eval Folder"})
    response = client.get("/folders/Eval%20Folder/evaluations/profile")
    assert response.status_code == 200
    assert response.json()["provider"] == "ollama"

    rejected = client.patch(
        "/folders/Eval%20Folder/evaluations/profile",
        json={"provider": "openai", "model_name": "gpt-4.1-mini", "auto_run_enabled": True},
    )
    assert rejected.status_code == 400

    updated = client.patch(
        "/folders/Eval%20Folder/evaluations/profile",
        json={"provider": "openai", "model_name": "gpt-4.1-mini", "auto_run_enabled": False},
    )
    assert updated.status_code == 200
    assert updated.json()["provider"] == "openai"
    assert updated.json()["model_name"] == "gpt-4.1-mini"


def test_eval_case_crud() -> None:
    client.post("/folders", json={"folder_name": "Eval Cases"})
    created = client.post(
        "/folders/Eval%20Cases/evaluations/cases",
        json={
            "name": "Definition",
            "question": "What is Pay10?",
            "reference_answer": "A payments platform",
            "expected_answer_points": ["payments", "platform"],
            "expected_source_files": ["faq.txt"],
            "tags": ["faq"],
            "case_type": "all",
            "enabled": True,
        },
    )
    assert created.status_code == 200
    case_id = created.json()["id"]

    listed = client.get("/folders/Eval%20Cases/evaluations/cases")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/folders/Eval%20Cases/evaluations/cases/{case_id}",
        json={
            "name": "Definition Updated",
            "question": "What is Pay10 really?",
            "reference_answer": "A payments platform",
            "expected_answer_points": ["payments", "platform"],
            "expected_source_files": ["faq.txt"],
            "tags": ["faq", "core"],
            "case_type": "answer",
            "enabled": True,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["case_type"] == "answer"

    deleted = client.delete(f"/folders/Eval%20Cases/evaluations/cases/{case_id}")
    assert deleted.status_code == 200


def test_ollama_models_endpoint(monkeypatch) -> None:
    from app.api import evaluations

    async def fake_models():
        return [{"name": "llama3.1", "size": 123, "modified_at": "today"}]

    monkeypatch.setattr(evaluations, "list_ollama_models", fake_models)
    response = client.get("/eval/providers/ollama/models")
    assert response.status_code == 200
    assert response.json()["models"][0]["name"] == "llama3.1"


def test_manual_eval_run_creation_does_not_persist_openai_key(monkeypatch) -> None:
    client.post("/folders", json={"folder_name": "Eval Run Folder"})
    client.patch(
        "/folders/Eval%20Run%20Folder/evaluations/profile",
        json={"provider": "openai", "model_name": "gpt-4.1-mini", "auto_run_enabled": False},
    )
    client.post(
        "/folders/Eval%20Run%20Folder/evaluations/cases",
        json={
            "name": "Definition",
            "question": "What is Pay10?",
            "reference_answer": "A payments platform",
            "expected_answer_points": ["payments", "platform"],
            "expected_source_files": ["faq.txt"],
            "tags": ["faq"],
            "case_type": "all",
            "enabled": True,
        },
    )
    enqueued: dict[str, str | None] = {}
    from app.api import evaluations

    monkeypatch.setattr(evaluations.eval_queue, "enqueue", lambda run_id, openai_api_key=None: enqueued.update({"run_id": run_id, "key": openai_api_key}))
    response = client.post(
        "/folders/Eval%20Run%20Folder/evaluations/runs",
        json={"run_type": "full", "provider": "openai", "model_name": "gpt-4.1-mini", "openai_api_key": "sk-secret"},
    )
    assert response.status_code == 200
    assert enqueued["key"] == "sk-secret"
    with SessionLocal() as db:
        folder = db.query(Folder).filter(Folder.normalized_name == "eval run folder").first()
        profile = db.query(EvalProfile).filter(EvalProfile.folder_id == folder.id).first()
        assert profile is not None
        assert not hasattr(profile, "openai_api_key")


def test_eval_run_execution_stores_items_and_artifacts(monkeypatch) -> None:
    client.post("/folders", json={"folder_name": "Executed Eval Folder"})
    client.post(
        "/folders/Executed%20Eval%20Folder/evaluations/cases",
        json={
            "name": "Definition",
            "question": "What is Pay10?",
            "reference_answer": "Pay10 is a payments platform.",
            "expected_answer_points": ["payments platform"],
            "expected_source_files": ["faq.txt"],
            "tags": ["faq"],
            "case_type": "all",
            "enabled": True,
        },
    )
    from app.services import eval_service

    monkeypatch.setattr(
        eval_service,
        "retrieve",
        lambda db, folder_name, query, top_k, max_top_k, timeout_seconds: SimpleNamespace(
            results=[
                SimpleNamespace(
                    content="Pay10 is a payments platform for merchants.",
                    metadata={"source_file": "faq.txt", "page_number": -1, "table_index": -1, "row_index": -1, "chunk_index": 0},
                )
            ],
            top_k=1,
        ),
    )

    async def fake_generate(**kwargs):
        return "Pay10 is a payments platform for merchants."

    monkeypatch.setattr(eval_service, "generate_eval_answer", fake_generate)

    with SessionLocal() as db:
        folder = db.query(Folder).filter(Folder.normalized_name == "executed eval folder").first()
        run = eval_service.create_eval_run(
            db=db,
            folder=folder,
            run_type=EvalRunType.FULL,
            trigger_type=EvalTriggerType.MANUAL,
            provider=folder.eval_profile.provider if folder.eval_profile else EvalProvider.OLLAMA,
            model_name="llama3.1",
        )
        eval_service.run_eval_job_sync(db, run.id)
        db.refresh(run)
        assert run.status == EvalRunStatus.COMPLETED
        assert run.summary_metrics["cases_evaluated"] == 1
        assert len(run.run_items) >= 2
        assert len(run.artifacts) == 1


def test_eval_run_failure_stores_clean_error_detail(monkeypatch) -> None:
    client.post("/folders", json={"folder_name": "Failed Eval Folder"})
    client.post(
        "/folders/Failed%20Eval%20Folder/evaluations/cases",
        json={
            "name": "Definition",
            "question": "What is Pay10?",
            "reference_answer": "Pay10 is a payments platform.",
            "expected_answer_points": ["payments platform"],
            "expected_source_files": ["faq.txt"],
            "tags": ["faq"],
            "case_type": "answer",
            "enabled": True,
        },
    )
    from app.services import eval_service

    monkeypatch.setattr(
        eval_service,
        "retrieve",
        lambda db, folder_name, query, top_k, max_top_k, timeout_seconds: SimpleNamespace(
            results=[
                SimpleNamespace(
                    content="Pay10 is a payments platform for merchants.",
                    metadata={"source_file": "faq.txt", "page_number": -1, "table_index": -1, "row_index": -1, "chunk_index": 0},
                )
            ],
            top_k=1,
        ),
    )

    async def failing_generate(**kwargs):
        raise HTTPException(status_code=503, detail="Ollama is not reachable at http://localhost:11434. Make sure Ollama is running and the base URL is correct.")

    monkeypatch.setattr(eval_service, "generate_eval_answer", failing_generate)

    with SessionLocal() as db:
        folder = db.query(Folder).filter(Folder.normalized_name == "failed eval folder").first()
        run = eval_service.create_eval_run(
            db=db,
            folder=folder,
            run_type=EvalRunType.ANSWER,
            trigger_type=EvalTriggerType.MANUAL,
            provider=EvalProvider.OLLAMA,
            model_name="llama3.1",
        )
        with pytest.raises(HTTPException):
            eval_service.run_eval_job_sync(db, run.id)
        db.refresh(run)
        assert run.status == EvalRunStatus.FAILED
        assert run.error_message == "Ollama is not reachable at http://localhost:11434. Make sure Ollama is running and the base URL is correct."


def test_auto_eval_run_is_created_after_index_when_enabled(monkeypatch) -> None:
    from app.services import indexing_service

    client.post("/folders", json={"folder_name": "Auto Eval Folder"})
    client.patch(
        "/folders/Auto%20Eval%20Folder/evaluations/profile",
        json={"provider": "ollama", "model_name": "llama3.1", "auto_run_enabled": True},
    )
    client.post(
        "/folders/Auto%20Eval%20Folder/upload",
        files=[("files", ("notes.txt", b"Pay10 is a payments platform.", "text/plain"))],
    )

    enqueued: dict[str, str | None] = {}
    monkeypatch.setattr(indexing_service, "_extract_blocks", lambda document: [{"text": "Pay10 is a payments platform.", "content_type": "text"}])
    monkeypatch.setattr(indexing_service, "embed_texts", lambda texts: [[0.1, 0.2, 0.3] for _ in texts])
    monkeypatch.setattr(indexing_service, "reset_collection", lambda collection_name: None)
    monkeypatch.setattr(indexing_service, "get_client", lambda: SimpleNamespace(upsert=lambda **kwargs: None))
    monkeypatch.setattr(indexing_service.eval_queue, "enqueue", lambda run_id, openai_api_key=None: enqueued.update({"run_id": run_id}))

    with SessionLocal() as db:
        folder = db.query(Folder).filter(Folder.normalized_name == "auto eval folder").first()
        assert folder is not None
        folder = db.query(Folder).filter(Folder.id == folder.id).first()
        indexing_service.index_folder(db, folder)

    assert "run_id" in enqueued
    with SessionLocal() as db:
        auto_run = db.query(EvalRun).filter(EvalRun.id == enqueued["run_id"]).first()
        assert auto_run is not None
        assert auto_run.trigger_type == EvalTriggerType.AUTO
        assert auto_run.run_type == EvalRunType.FULL
