"""POST /ask."""

from __future__ import annotations

import time
import uuid
from typing import Annotated

from asgi_correlation_id import correlation_id
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.core.metrics import ask_latency_seconds, ask_requests_total
from app.core.observability import trace_ask
from app.deps import get_graph
from app.schemas.ask import AskRequest, AskResponse, Source
from app.utils.auth import require_bearer

router = APIRouter(tags=["ask"])
_bearer = HTTPBearer(auto_error=False)


@router.post("/ask", response_model=AskResponse)
@limiter.limit("30/minute")
def ask(
    request: Request,
    body: AskRequest,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> AskResponse:
    if settings.AUTH_REQUIRED:
        require_bearer(credentials)
    trace_id = correlation_id.get() or uuid.uuid4().hex
    started = time.perf_counter()
    try:
        with trace_ask(trace_id, body.question):
            result = get_graph().invoke(body.question, top_k=body.top_k)
    except Exception as exc:
        ask_requests_total.labels(abstained="false", status="error").inc()
        logger.exception("ask_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The question could not be answered.",
        ) from exc
    elapsed = time.perf_counter() - started
    ask_latency_seconds.observe(elapsed)
    abstained = bool(result.get("abstained"))
    ask_requests_total.labels(abstained=str(abstained).lower(), status="ok").inc()
    sources = [Source(**item) for item in result.get("sources") or []]
    return AskResponse(
        answer=result.get("answer", ""),
        sources=sources,
        latency_ms=round(elapsed * 1000, 1),
        trace_id=trace_id,
        abstained=abstained,
    )
