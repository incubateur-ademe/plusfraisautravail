import os

os.environ.setdefault("VIGILANCE_APP_ID", "test-app-id")

from fastapi.testclient import TestClient  # noqa: E402

from pfat_api.main import app  # noqa: E402


def test_health() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
