"""Application entry point."""

from multiprocessing import cpu_count

import uvicorn
import uvloop
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from core.config import AppConfig, configure_logging


def create_app() -> Starlette:
    """Create Starlette application."""

    async def healthcheck(request) -> JSONResponse:
        return JSONResponse({"status": "ok"}, status_code=202)

    return Starlette(routes=[Route("/health", healthcheck, methods=["GET"])])


config = AppConfig()
configure_logging()
app = create_app()


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
