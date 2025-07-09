import asyncio
import contextlib
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from core.config import AppConfig
from service.task_processor import process_tasks
from tasks.models import TaskPayload, TaskMessage, TraceContext


@pytest.mark.asyncio
async def test_should_process_task_asynchronously() -> None:
    config = AppConfig()
    message = TaskMessage(
        task_id="1",
        timestamp="2025-01-01T00:00:00Z",
        payload=TaskPayload(data="foo", metadata={}),
        trace_context=TraceContext(trace_id="t", span_id="s"),
    )
    redis_mock = AsyncMock()
    redis_mock.__aenter__.return_value = redis_mock
    redis_mock.__aexit__.return_value = False
    redis_mock.xgroup_create = AsyncMock()
    redis_mock.xack = AsyncMock()
    redis_mock.xdel = AsyncMock()
    redis_mock.xreadgroup = AsyncMock(
        side_effect=[
            [
                (
                    config.redis_stream_name.encode(),
                    [(b"1-0", {b"task": message.model_dump_json().encode()})],
                )
            ],
            asyncio.CancelledError(),
        ]
    )
    handled = []

    async def handler(msg: TaskMessage) -> None:
        handled.append(msg.task_id)

    with patch("service.task_processor.Redis.from_url", return_value=redis_mock):
        shutdown_event = asyncio.Event()
        task = asyncio.create_task(process_tasks(config, handler, shutdown_event))
        await asyncio.sleep(0)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    assert handled == ["1"]
    redis_mock.xack.assert_called_once_with(
        config.redis_stream_name, config.redis_consumer_group, b"1-0"
    )
    redis_mock.xdel.assert_called_once_with(config.redis_stream_name, b"1-0")
