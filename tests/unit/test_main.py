from pathlib import Path
import sys
import json
from loguru import logger
from starlette.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from core.config import configure_logging
from main import app


def test_should_return_202_when_health_requested() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 202
    assert response.json() == {"status": "ok"}


def test_should_output_json_when_logging_configured(capsys) -> None:
    configure_logging()
    logger.bind(task_id="1", trace_id="abc").info("test")
    log_line = capsys.readouterr().out.strip()
    record = json.loads(log_line)
    assert record["level"] == "INFO"
    assert record["message"] == "test"
