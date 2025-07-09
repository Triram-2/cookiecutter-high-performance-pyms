from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .models import TaskMessage, TaskPayload, TraceContext
from .repository import TaskRepository


class TaskService:
    """Service layer for task operations."""

    def __init__(self, repo: TaskRepository) -> None:
        self._repo = repo

    async def enqueue(
        self, payload: TaskPayload, trace_id: str = "", span_id: str = ""
    ) -> None:
        """Create and store task message."""
        message = TaskMessage(
            task_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload,
            trace_context=TraceContext(trace_id=trace_id, span_id=span_id),
        )
        await self._repo.add(message)
