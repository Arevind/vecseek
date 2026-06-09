from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from app.config import get_settings
from app.models import EvalProvider
from app.utils.errors import bad_gateway, bad_request, gateway_timeout, service_unavailable, unauthorized


def build_eval_prompt(question: str, retrieval_results: list[dict[str, Any]]) -> str:
    context = "\n\n".join(
        [
            f"Source: {item.get('source_file', 'unknown')} | Page: {item.get('page_number', -1)}\n{item.get('content', '')}"
            for item in retrieval_results
        ]
    )
    return (
        "You are answering only from the provided workspace context.\n"
        "If the answer is not supported by the context, say so briefly.\n\n"
        f"Question:\n{question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer:"
    )


def _extract_provider_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            detail = payload.get("error") or payload.get("message") or payload.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail.strip()
    except ValueError:
        pass
    return response.text.strip()


def _map_ollama_http_error(exc: httpx.HTTPStatusError, base_url: str, model_name: str | None) -> HTTPException:
    response = exc.response
    detail = _extract_provider_error(response)
    lowered = detail.lower()
    if response.status_code == 404 and model_name and "not found" in lowered:
        return bad_request(
            f'The Ollama model "{model_name}" is not available. Pull it first or choose a different downloaded model.'
        )
    if response.status_code == 404:
        return service_unavailable(
            f"Ollama responded, but the required API endpoint was not found at {base_url}. Check that the Ollama base URL is correct."
        )
    if response.status_code >= 500:
        return bad_gateway("Ollama returned a server error while VecSeek was generating an evaluation answer.")
    return bad_gateway(f"Ollama returned an unexpected error: {detail or response.reason_phrase}")


def _map_openai_http_error(exc: httpx.HTTPStatusError, model_name: str) -> HTTPException:
    response = exc.response
    detail = _extract_provider_error(response)
    lowered = detail.lower()
    if response.status_code in {401, 403}:
        return unauthorized("OpenAI rejected the provided API key. Check that the key is valid and has access to this model.")
    if response.status_code == 404 or ("model" in lowered and "not found" in lowered):
        return bad_request(f'The OpenAI model "{model_name}" is not available for this API key or does not exist.')
    if response.status_code == 429:
        return service_unavailable("OpenAI rate limits are currently being hit. Wait a moment and try the evaluation again.")
    if response.status_code >= 500:
        return bad_gateway("OpenAI is currently unavailable or returned a server error. Please try again shortly.")
    return bad_gateway(f"OpenAI returned an unexpected error: {detail or response.reason_phrase}")


async def list_ollama_models() -> list[dict[str, Any]]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
            payload = response.json()
    except httpx.ConnectError as exc:
        raise service_unavailable(
            f"Ollama is not reachable at {settings.ollama_base_url}. Make sure Ollama is running and the base URL is correct."
        ) from exc
    except httpx.TimeoutException as exc:
        raise gateway_timeout(
            f"Ollama did not respond in time at {settings.ollama_base_url}. Make sure the server is healthy and try again."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise _map_ollama_http_error(exc, settings.ollama_base_url, model_name=None) from exc
    except httpx.RequestError as exc:
        raise bad_gateway(
            f"VecSeek could not contact Ollama at {settings.ollama_base_url}. Check the Ollama server and your network connection."
        ) from exc

    models = payload.get("models", [])
    return [
        {
            "name": str(item.get("name", "")),
            "size": item.get("size"),
            "modified_at": item.get("modified_at"),
        }
        for item in models
        if item.get("name")
    ]


async def generate_eval_answer(
    provider: EvalProvider,
    model_name: str,
    question: str,
    retrieval_results: list[dict[str, Any]],
    openai_api_key: str | None = None,
) -> str:
    prompt = build_eval_prompt(question, retrieval_results)
    settings = get_settings()
    if provider == EvalProvider.OLLAMA:
        try:
            async with httpx.AsyncClient(timeout=settings.eval_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                    json={"model": model_name, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                return str(response.json().get("response", "")).strip()
        except httpx.ConnectError as exc:
            raise service_unavailable(
                f"Ollama is not reachable at {settings.ollama_base_url}. Start Ollama before running answer or red-team evaluations."
            ) from exc
        except httpx.TimeoutException as exc:
            raise gateway_timeout(
                f'Ollama did not respond in time while generating with "{model_name}". Make sure the model is loaded and try again.'
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise _map_ollama_http_error(exc, settings.ollama_base_url, model_name=model_name) from exc
        except httpx.RequestError as exc:
            raise bad_gateway(
                "VecSeek could not complete the Ollama evaluation request. Check the Ollama server and your network connection."
            ) from exc

    if provider == EvalProvider.OPENAI:
        if not openai_api_key:
            raise bad_request("An OpenAI API key is required for OpenAI evaluation runs.")
        try:
            async with httpx.AsyncClient(timeout=settings.eval_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.openai_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {openai_api_key}"},
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": "Answer only from the provided context. Be concise and factual."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                return str(payload["choices"][0]["message"]["content"]).strip()
        except httpx.ConnectError as exc:
            raise service_unavailable(
                "OpenAI could not be reached. Check that internet access is available and that the OpenAI base URL is correct."
            ) from exc
        except httpx.TimeoutException as exc:
            raise gateway_timeout(
                f'OpenAI did not respond in time while generating with "{model_name}". Please try again.'
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise _map_openai_http_error(exc, model_name=model_name) from exc
        except httpx.RequestError as exc:
            raise bad_gateway(
                "VecSeek could not complete the OpenAI evaluation request. Check your internet connection and provider settings."
            ) from exc

    raise bad_request("Unsupported evaluation provider.")
