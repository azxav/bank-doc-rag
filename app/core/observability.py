"""Optional Langfuse tracing. No-op when keys or the package are absent."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from app.core.config import settings
from app.core.logging import logger


def tracing_enabled() -> bool:
    return bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)


@contextmanager
def trace_ask(trace_id: str, question: str) -> Iterator[None]:
    """Open a Langfuse span when configured. Failures are logged and ignored."""
    if not tracing_enabled():
        yield
        return
    try:
        from langfuse import Langfuse
    except Exception:
        logger.warning("langfuse_import_unavailable")
        yield
        return
    try:
        client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
    except Exception:
        logger.warning("langfuse_init_failed")
        yield
        return
    try:
        if hasattr(client, "start_as_current_span"):
            with client.start_as_current_span(name="ask", trace_context={"trace_id": trace_id}):
                yield
        else:
            yield
    except Exception:
        logger.warning("langfuse_span_failed", trace_id=trace_id)
        yield
    finally:
        try:
            client.flush()
        except Exception:
            logger.warning("langfuse_flush_failed")
