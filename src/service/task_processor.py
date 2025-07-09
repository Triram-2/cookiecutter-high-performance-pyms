from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from loguru import logger
from redis.asyncio import Redis

from core.config import AppConfig
from tasks.models import TaskMessage


AsyncHandler = Callable[[TaskMessage], Awaitable[None]]


async def process_tasks(
    config: AppConfig, handler: AsyncHandler, shutdown_event: asyncio.Event
) -> None:
    """Continuously read and process tasks from Redis Streams."""

    stream = config.redis_stream_name
    group = config.redis_consumer_group
    consumer = config.redis_consumer_name

    redis = Redis.from_url(config.redis_url)
    async with redis:
        try:
            await redis.xgroup_create(stream, group, mkstream=True)
        except Exception:
            # Group might already exist
            pass

        logger.info(f"Connected to Redis stream {stream}")

        while not shutdown_event.is_set():
            try:
                records = await redis.xreadgroup(
                    group,
                    consumer,
                    streams={stream: ">"},
                    count=1,
                    block=1000,
                )
                if not records:
                    continue

                for _, messages in records:
                    for message_id, data in messages:
                        raw = data.get(b"task", b"{}").decode()
                        try:
                            task = TaskMessage.model_validate_json(raw)
                        except Exception as exc:
                            logger.error(f"Invalid task data: {exc}")
                            await redis.xack(stream, group, message_id)
                            await redis.xdel(stream, message_id)
                            continue

                        for attempt, delay in enumerate((0.1, 0.2, 0.4), start=1):
                            try:
                                await handler(task)
                                await redis.xack(stream, group, message_id)
                                await redis.xdel(stream, message_id)
                                break
                            except Exception as exc:
                                logger.error(f"Task processing failed: {exc}")
                                if attempt == 3:
                                    await redis.xack(stream, group, message_id)
                                    await redis.xdel(stream, message_id)
                                else:
                                    await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(f"Processor error: {exc}")
                await asyncio.sleep(1)
