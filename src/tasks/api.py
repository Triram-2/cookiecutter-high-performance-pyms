from __future__ import annotations

from pydantic import ValidationError
from redis.asyncio import Redis
from starlette.requests import Request
from starlette.responses import Response

from core.config import AppConfig
from .models import TaskPayload
from .repository import TaskRepository
from .service import TaskService


async def create_task(request: Request, config: AppConfig) -> Response:
    """Validate request and enqueue task."""
    body = await request.body()
    if len(body) > config.max_payload_size:
        return Response(status_code=413)

    try:
        payload = TaskPayload.model_validate_json(body)
    except ValidationError:
        return Response(status_code=400)

    trace_id = request.headers.get("trace_id", "")
    span_id = request.headers.get("span_id", "")

    async with Redis.from_url(config.redis_url) as redis:
        repo = TaskRepository(redis, config.redis_stream_name)
        service = TaskService(repo)
        await service.enqueue(payload, trace_id=trace_id, span_id=span_id)

    return Response(status_code=202)
