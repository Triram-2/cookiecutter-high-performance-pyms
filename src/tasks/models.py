from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel, Field


class TaskPayload(BaseModel):
    """Payload data for a task."""

    data: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TraceContext(BaseModel):
    """Tracing information for a task."""

    trace_id: str
    span_id: str


class TaskMessage(BaseModel):
    """Message structure stored in Redis Streams."""

    task_id: str
    timestamp: str
    payload: TaskPayload
    trace_context: TraceContext
