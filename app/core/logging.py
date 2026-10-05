"""Structured logging. JSON in production, console otherwise."""

from __future__ import annotations

import logging

import structlog

from app.core.config import Environment, settings


def setup_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(message)s")
    renderer: structlog.types.Processor
    if settings.ENVIRONMENT is Environment.PRODUCTION:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


setup_logging()
logger = structlog.get_logger("bank_doc_rag")
