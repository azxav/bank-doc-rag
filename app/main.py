"""FastAPI entrypoint for the bank-document RAG service."""

from datetime import datetime, timezone

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import api_router
from app.api.v1.ask import router as ask_router
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.core.metrics import metrics_response
from app.deps import get_store

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ask_router)


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.get("/")
def root() -> dict:
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT.value,
        "docs": "/docs",
        "ask": "/ask",
    }


@app.get("/health")
def health() -> dict:
    qdrant_ok = get_store().ping()
    payload = {
        "status": "healthy" if qdrant_ok else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT.value,
        "components": {
            "api": "healthy",
            "qdrant": "healthy" if qdrant_ok else "unhealthy",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if not qdrant_ok:
        return JSONResponse(status_code=503, content=payload)
    logger.info("health_ok")
    return payload
