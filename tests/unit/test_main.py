from pathlib import Path
import sys
import json
from loguru import logger
from starlette.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from core.config import configure_logging
from main import app, config
from unittest.mock import AsyncMock, patch
from datetime import datetime


def test_should_return_ok_when_redis_available() -> None:
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
