from __future__ import annotations

import importlib
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from loguru import logger
from starlette.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from core.config import configure_logging


def _load_app():
    with patch("core.tracing.configure_tracing"):
        import main
        importlib.reload(main)
    return main.app, main.config


def test_should_return_ok_when_redis_available() -> None:
    app, config = _load_app()
    redis_mock = AsyncMock()
    redis_mock.__aenter__.return_value = redis_mock
    redis_mock.__aexit__.return_value = False
    redis_mock.ping = AsyncMock(return_value=True)

    with patch("main.Redis.from_url", return_value=redis_mock):
        client = TestClient(app)
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["redis_connected"] is True
    assert body["version"] == config.service_version
    datetime.fromisoformat(body["timestamp"])


def test_should_output_json_when_logging_configured(capsys) -> None:
    configure_logging()
    logger.bind(task_id="1", trace_id="abc").info("test")
    log_line = capsys.readouterr().out.strip()
    record = json.loads(log_line)
    assert record["level"] == "INFO"
    assert record["message"] == "test"
    with open("loki.log") as fh:
        assert "test" in fh.read()


def test_should_send_metrics_via_statsd() -> None:
    app, _ = _load_app()
    with patch("core.metrics.statsd_client") as statsd:
        statsd.incr = MagicMock()
        statsd.timing = MagicMock()
        client = TestClient(app)
        client.get("/health")
        statsd.incr.assert_called_with("request_count")


def test_should_create_tracing_span() -> None:
    app, _ = _load_app()
    with patch("core.tracing.tracer.start_as_current_span") as span:
        span.return_value.__enter__.return_value = None
        span.return_value.__exit__.return_value = False
        client = TestClient(app)
        client.get("/health")
        span.assert_called_with("api_request_span")
