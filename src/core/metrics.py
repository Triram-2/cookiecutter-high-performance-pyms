from __future__ import annotations

import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from statsd import StatsClient

from .config import AppConfig

statsd_client: Optional[StatsClient] = None


def init_metrics(config: AppConfig) -> None:
    """Initialize StatsD client from application config."""
    global statsd_client
    statsd_client = StatsClient(
        host=config.statsd_host,
        port=config.statsd_port,
        prefix=config.statsd_prefix,
    )


class StatsDMiddleware(BaseHTTPMiddleware):
    """Middleware that sends request metrics to StatsD."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        start = time.perf_counter()
        response = await call_next(request)
        if statsd_client is not None:
            duration = int((time.perf_counter() - start) * 1000)
            statsd_client.incr("request_count")
            statsd_client.timing("request_duration", duration)
        return response
