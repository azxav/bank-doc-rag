"""Prometheus metrics for the API process."""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

ask_requests_total = Counter(
    "ask_requests_total",
    "POST /ask calls",
    ["abstained", "status"],
)
ask_latency_seconds = Histogram(
    "ask_latency_seconds",
    "End-to-end /ask latency",
    buckets=(0.1, 0.3, 0.5, 1, 2, 5, 10, 30, 60),
)
llm_call_seconds = Histogram(
    "llm_call_seconds",
    "OpenRouter chat latency",
    ["operation"],
    buckets=(0.1, 0.3, 0.5, 1, 2, 5, 10, 30),
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
