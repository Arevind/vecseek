import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.models import EvalProvider
from app.services import eval_generation


class _ConnectClient:
    def __init__(self, *args, **kwargs):  # noqa: ARG002
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ARG002
        return False

    async def get(self, url):  # noqa: ARG002
        raise httpx.ConnectError("connection failed")


class _OllamaMissingModelClient:
    def __init__(self, *args, **kwargs):  # noqa: ARG002
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ARG002
        return False

    async def post(self, url, json):  # noqa: ARG002
        request = httpx.Request("POST", url)
        response = httpx.Response(404, request=request, json={"error": f'model "{json["model"]}" not found'})
        raise httpx.HTTPStatusError("model missing", request=request, response=response)


class _OpenAiUnauthorizedClient:
    def __init__(self, *args, **kwargs):  # noqa: ARG002
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ARG002
        return False

    async def post(self, url, headers, json):  # noqa: ARG002
        request = httpx.Request("POST", url, headers=headers)
        response = httpx.Response(401, request=request, json={"error": "Incorrect API key provided"})
        raise httpx.HTTPStatusError("unauthorized", request=request, response=response)


def test_list_ollama_models_returns_friendly_connection_error(monkeypatch) -> None:
    monkeypatch.setattr(eval_generation.httpx, "AsyncClient", _ConnectClient)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(eval_generation.list_ollama_models())
    assert exc_info.value.status_code == 503
    assert "Ollama is not reachable" in str(exc_info.value.detail)


def test_generate_eval_answer_returns_friendly_invalid_ollama_model_error(monkeypatch) -> None:
    monkeypatch.setattr(eval_generation.httpx, "AsyncClient", _OllamaMissingModelClient)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            eval_generation.generate_eval_answer(
                provider=EvalProvider.OLLAMA,
                model_name="missing-model",
                question="What is Pay10?",
                retrieval_results=[{"content": "Pay10 is a gateway.", "source_file": "faq.txt", "page_number": -1}],
            )
        )
    assert exc_info.value.status_code == 400
    assert 'The Ollama model "missing-model" is not available' in str(exc_info.value.detail)


def test_generate_eval_answer_returns_friendly_openai_auth_error(monkeypatch) -> None:
    monkeypatch.setattr(eval_generation.httpx, "AsyncClient", _OpenAiUnauthorizedClient)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            eval_generation.generate_eval_answer(
                provider=EvalProvider.OPENAI,
                model_name="gpt-4.1-mini",
                question="What is Pay10?",
                retrieval_results=[{"content": "Pay10 is a gateway.", "source_file": "faq.txt", "page_number": -1}],
                openai_api_key="bad-key",
            )
        )
    assert exc_info.value.status_code == 401
    assert "OpenAI rejected the provided API key" in str(exc_info.value.detail)
