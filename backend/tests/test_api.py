import os
import tempfile

from fastapi.testclient import TestClient

temp_dir = tempfile.mkdtemp(prefix="kb-studio-tests-")
os.environ["UPLOAD_DIR"] = os.path.join(temp_dir, "uploads")
os.environ["QDRANT_DIR"] = os.path.join(temp_dir, "qdrant")
os.environ["SQLITE_PATH"] = os.path.join(temp_dir, "knowledgebase.db")

from app.config import get_settings as _settings_factory  # noqa: E402
from app.main import app

_settings_factory.cache_clear()


client = TestClient(app)

def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_folder_and_reject_duplicate() -> None:
    response = client.post("/folders", json={"folder_name": "Aadhaar SOP Docs"})
    assert response.status_code == 200
    duplicate = client.post("/folders", json={"folder_name": "aadhaar sop docs"})
    assert duplicate.status_code == 409


def test_settings_validation() -> None:
    response = client.patch("/settings", json={"default_top_k": 999, "chunk_size": 1400, "chunk_overlap": 250})
    assert response.status_code == 400


def test_settings_reject_overlap_greater_than_size() -> None:
    response = client.patch("/settings", json={"default_top_k": 5, "chunk_size": 400, "chunk_overlap": 400})
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
