from pathlib import Path
import sys
from starlette.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from main import app


def test_should_return_202_when_health_requested() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 202
    assert response.json() == {"status": "ok"}
