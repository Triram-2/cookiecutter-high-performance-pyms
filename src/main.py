"""Application entry point."""

from multiprocessing import cpu_count

import uvicorn
import uvloop
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.requests import Request

from datetime import datetime
from redis.asyncio import Redis
from loguru import logger
import asyncio
import contextlib

from core.config import AppConfig, configure_logging
from pydantic import BaseModel
from tasks.api import create_task
from service.task_processor import process_tasks
from tasks.models import TaskMessage


class HealthResponse(BaseModel):
    """API response schema for health checks."""

    status: str
    timestamp: str
    redis_connected: bool
    version: str


def create_app() -> Starlette:
    """Create Starlette application."""

    async def healthcheck(request: Request) -> JSONResponse:
        """Return health information about the service."""

        redis_connected = False
        try:
            async with Redis.from_url(config.redis_url) as redis:
                await redis.ping()
                redis_connected = True
        except Exception:
            redis_connected = False

        status = "healthy" if redis_connected else "unhealthy"
        response = HealthResponse(
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            redis_connected=redis_connected,
            version=config.service_version,
        )
        status_code = 200 if redis_connected else 503
        return JSONResponse(response.model_dump(), status_code=status_code)

    async def tasks(request: Request) -> Response:
        return await create_task(request, config)

    return Starlette(
        routes=[
            Route("/health", healthcheck, methods=["GET"]),
            Route("/tasks", tasks, methods=["POST"]),
        ]
    )


config = AppConfig()
configure_logging()
app = create_app()


async def _log_task(message: TaskMessage) -> None:
    """Default task handler that logs the task."""

    logger.bind(task_id=message.task_id, trace_id=message.trace_context.trace_id).info(
        "processed"
    )


@app.on_event("startup")
async def _start_processor() -> None:
    app.state.processor_task = asyncio.create_task(process_tasks(config, _log_task))


@app.on_event("shutdown")
async def _stop_processor() -> None:
    app.state.processor_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await app.state.processor_task


def _get_workers(cfg: AppConfig) -> int:
    """Return number of worker processes."""

    return cpu_count() if cfg.worker_processes == "auto" else int(cfg.worker_processes)


if __name__ == "__main__":
    loop_type = "uvloop" if config.uvloop_enabled else "asyncio"
    if config.uvloop_enabled:
        uvloop.install()
    uvicorn.run(
        "main:app",
        host=config.service_host,
        port=config.service_port,
        loop=loop_type,
        workers=_get_workers(config),
    )
