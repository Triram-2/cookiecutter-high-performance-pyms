from __future__ import annotations

from redis.asyncio import Redis

from .models import TaskMessage


class TaskRepository:
    """Repository for storing tasks in Redis Streams."""

    def __init__(self, redis: Redis, stream_name: str) -> None:
        self._redis = redis
        self._stream = stream_name

    async def add(self, message: TaskMessage) -> None:
        """Add message to Redis stream."""
        await self._redis.xadd(
            self._stream,
            {"task": message.model_dump_json()},
            maxlen=100000,
        )
