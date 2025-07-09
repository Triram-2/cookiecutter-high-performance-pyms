from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

from core.config import settings
from core.logging_config import configure_logging


def create_app() -> Starlette:
    """Create Starlette application."""
    configure_logging()

    async def healthcheck(request) -> JSONResponse:
        return JSONResponse({"status": "ok"}, status_code=202)

    return Starlette(routes=[Route("/health", healthcheck, methods=["GET"])])


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port)
