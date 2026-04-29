from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from pfat_api.main import app
from pfat_api.routes import alerts as alerts_module
from pfat_api.schemas import DepartmentAlert, HeatwaveSnapshot, Severity
from pfat_api.sources.meteofrance import UpstreamError


def _make_snapshot() -> HeatwaveSnapshot:
    return HeatwaveSnapshot(
        departments=[
            DepartmentAlert(code="01", day1=Severity.VERT, day2=Severity.VERT),
            DepartmentAlert(code="2A", day1=Severity.JAUNE, day2=Severity.VERT),
            DepartmentAlert(code="75", day1=Severity.ORANGE, day2=Severity.JAUNE),
        ],
        fetched_at=datetime(2026, 4, 30, 12, 0, tzinfo=UTC),
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Stub the heatwave loader and reset the module-level cache between tests."""
    snapshot = _make_snapshot()

    async def fake_loader() -> HeatwaveSnapshot:
        return snapshot

    cache = alerts_module._heatwave_cache
    monkeypatch.setattr(cache, "_loader", fake_loader)
    monkeypatch.setattr(cache, "_value", None)
    monkeypatch.setattr(cache, "_loaded_at", 0.0)

    with TestClient(app) as c:
        yield c


def test_get_heatwave_returns_all_departments(client: TestClient) -> None:
    resp = client.get("/alerts/heatwave")
    assert resp.status_code == 200
    body = resp.json()
    assert body["phenomenon"] == "canicule"
    assert body["phenomenon_id"] == "8"
    assert body["source"] == "meteofrance.vigilance"
    codes = [d["code"] for d in body["departments"]]
    assert codes == ["01", "2A", "75"]


def test_get_heatwave_for_department_match(client: TestClient) -> None:
    resp = client.get("/alerts/heatwave/75")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["departments"]) == 1
    assert body["departments"][0] == {"code": "75", "day1": "orange", "day2": "jaune"}


def test_get_heatwave_for_department_corsica_uppercased(client: TestClient) -> None:
    resp = client.get("/alerts/heatwave/2a")
    assert resp.status_code == 200
    body = resp.json()
    assert body["departments"][0]["code"] == "2A"


def test_get_heatwave_for_unknown_department_returns_404(client: TestClient) -> None:
    resp = client.get("/alerts/heatwave/99")
    assert resp.status_code == 404
    assert "99" in resp.json()["detail"]


def test_sources_unhealthy_before_first_fetch(client: TestClient) -> None:
    resp = client.get("/sources")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "meteofrance.vigilance"
    assert body[0]["healthy"] is False
    assert body[0]["last_refresh"] is None


def test_sources_healthy_after_fetch(client: TestClient) -> None:
    assert client.get("/alerts/heatwave").status_code == 200
    resp = client.get("/sources")
    body = resp.json()
    assert body[0]["healthy"] is True
    assert body[0]["last_refresh"] is not None


def test_upstream_error_returns_502(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_loader() -> HeatwaveSnapshot:
        raise UpstreamError("VIGILANCE_APP_ID is malformed")

    monkeypatch.setattr(alerts_module._heatwave_cache, "_loader", failing_loader)
    monkeypatch.setattr(alerts_module._heatwave_cache, "_value", None)
    monkeypatch.setattr(alerts_module._heatwave_cache, "_loaded_at", 0.0)

    resp = client.get("/alerts/heatwave")
    assert resp.status_code == 502
    assert "VIGILANCE_APP_ID" in resp.json()["detail"]

    resp = client.get("/alerts/heatwave/75")
    assert resp.status_code == 502


def test_cache_reuses_value_within_ttl(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}
    snapshot = _make_snapshot()

    async def counting_loader() -> HeatwaveSnapshot:
        calls["n"] += 1
        return snapshot

    monkeypatch.setattr(alerts_module._heatwave_cache, "_loader", counting_loader)

    client.get("/alerts/heatwave")
    client.get("/alerts/heatwave")
    client.get("/alerts/heatwave/75")

    assert calls["n"] == 1
