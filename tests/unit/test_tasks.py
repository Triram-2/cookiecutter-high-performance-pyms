from pathlib import Path
import sys
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from main import app, config


def test_should_respond_202_when_post_task() -> None:
    redis_mock = AsyncMock()
    redis_mock.__aenter__.return_value = redis_mock
    redis_mock.__aexit__.return_value = False
    redis_mock.xadd = AsyncMock(return_value=b"1-0")

    with patch("main.Redis.from_url", return_value=redis_mock):
        client = TestClient(app)
        response = client.post("/tasks", json={"data": "foo", "metadata": {}})

    assert response.status_code == 202
    redis_mock.xadd.assert_called_once()
    args, _ = redis_mock.xadd.call_args
    assert args[0] == config.redis_stream_name


def test_should_return_413_when_payload_too_large() -> None:
    client = TestClient(app)
    big_body = b"x" * (config.max_payload_size + 1)
    response = client.post(
        "/tasks", data=big_body, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 413
