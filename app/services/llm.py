"""OpenRouter chat and embedding clients."""

from __future__ import annotations

import re
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import llm_call_seconds
from app.services.models import choose_chat_model


class OpenRouterError(RuntimeError):
    pass


def _affordable_tokens(body: str) -> int | None:
    match = re.search(r"can only afford (\d+)", body)
    if not match:
        return None
    return int(match.group(1))


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/azxav/bank-doc-rag",
        "X-Title": "bank-doc-rag",
    }


class OpenRouterChat:
    """Chat completions against OpenRouter. Falls back once on a model 404."""

    def __init__(self, model: str | None = None) -> None:
        self.preferred_model = model or settings.CHAT_MODEL
        self.resolved_model = self.preferred_model

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 220,
        json_mode: bool = False,
        operation: str = "chat",
    ) -> str:
        if not settings.OPENROUTER_API_KEY:
            raise OpenRouterError("OPENROUTER_API_KEY is not set")
        return self._complete(
            self.resolved_model,
            system,
            user,
            max_tokens=max_tokens,
            json_mode=json_mode,
            operation=operation,
            allow_fallback=True,
            allow_plain_retry=json_mode,
            allow_credit_retry=True,
        )

    def _complete(
        self,
        model: str,
        system: str,
        user: str,
        *,
        max_tokens: int,
        json_mode: bool,
        operation: str,
        allow_fallback: bool,
        allow_plain_retry: bool,
        allow_credit_retry: bool,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "temperature": 0,
            "max_tokens": max_tokens,
            "reasoning": {"effort": "minimal"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        started = time.perf_counter()
        response = httpx.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        llm_call_seconds.labels(operation=operation).observe(time.perf_counter() - started)
        if response.status_code == 404 and allow_fallback:
            self.resolved_model = self._fallback_model()
            logger.warning(
                "chat_model_fallback",
                preferred=self.preferred_model,
                resolved=self.resolved_model,
            )
            return self._complete(
                self.resolved_model,
                system,
                user,
                max_tokens=max_tokens,
                json_mode=json_mode,
                operation=operation,
                allow_fallback=False,
                allow_plain_retry=allow_plain_retry,
                allow_credit_retry=allow_credit_retry,
            )
        if response.status_code == 402 and allow_credit_retry:
            affordable = _affordable_tokens(response.text)
            if affordable is not None and affordable >= 32 and affordable < max_tokens:
                logger.warning("lowering_max_tokens", requested=max_tokens, affordable=affordable)
                return self._complete(
                    model,
                    system,
                    user,
                    max_tokens=affordable,
                    json_mode=json_mode,
                    operation=operation,
                    allow_fallback=allow_fallback,
                    allow_plain_retry=allow_plain_retry,
                    allow_credit_retry=False,
                )
        if response.status_code == 400 and json_mode and allow_plain_retry:
            return self._complete(
                model,
                system,
                user,
                max_tokens=max_tokens,
                json_mode=False,
                operation=operation,
                allow_fallback=allow_fallback,
                allow_plain_retry=False,
                allow_credit_retry=allow_credit_retry,
            )
        if response.status_code >= 400:
            detail = re.sub(r"https://\S+", "[redacted-url]", response.text)[:300]
            raise OpenRouterError(f"OpenRouter chat failed ({response.status_code}): {detail}")
        message = response.json()["choices"][0]["message"]
        content = message.get("content")
        if not content:
            raise OpenRouterError("OpenRouter returned an empty chat message")
        return content

    def _fallback_model(self) -> str:
        response = httpx.get(
            f"{settings.OPENROUTER_BASE_URL}/models",
            headers=_headers(),
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        if response.status_code >= 400:
            raise OpenRouterError(
                f"Could not list OpenRouter models ({response.status_code}) "
                f"after {self.preferred_model} returned 404"
            )
        ids = {item["id"] for item in response.json().get("data", []) if "id" in item}
        return choose_chat_model(self.preferred_model, ids)


class OpenRouterEmbeddings:
    def __init__(self) -> None:
        self.model_name = settings.EMBEDDING_MODEL

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 16):
            vectors.extend(self._embed_batch(texts[start : start + 16]))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not settings.OPENROUTER_API_KEY:
            raise OpenRouterError("OPENROUTER_API_KEY is not set")
        response = httpx.post(
            f"{settings.OPENROUTER_BASE_URL}/embeddings",
            headers=_headers(),
            json={"model": settings.EMBEDDING_MODEL, "input": texts},
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        if response.status_code >= 400:
            detail = re.sub(r"https://\S+", "[redacted-url]", response.text)[:300]
            raise OpenRouterError(
                f"OpenRouter embeddings failed ({response.status_code}): {detail}"
            )
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        vectors = [item["embedding"] for item in data]
        if len(vectors) != len(texts):
            raise OpenRouterError("Embedding response did not cover every input")
        return vectors


class HashEmbeddings:
    """Deterministic bag-of-tokens vectors for tests and the offline demo."""

    model_name = "hash-bag-of-tokens"

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        import math
        import zlib

        from app.services.sparse import tokenize

        vector = [0.0] * self.dim
        for token in tokenize(text):
            vector[zlib.crc32(token.encode("utf-8")) % self.dim] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
