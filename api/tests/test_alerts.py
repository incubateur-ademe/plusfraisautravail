from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from pfat_api.main import app
from pfat_api.routes import alerts as alerts_module
from pfat_api.schemas import (
    DepartmentMeteoAlert,
    MeteoSnapshot,
    PhenomenonAlert,
    Severity,
)
from pfat_api.sources.meteofrance import UpstreamError


def _make_snapshot(*, active: bool = True) -> MeteoSnapshot:
    if not active:
        return MeteoSnapshot(
            active=False,
            departments=[],
            fetched_at=datetime(2026, 4, 30, 12, 0, tzinfo=UTC),
        )
    return MeteoSnapshot(
        active=True,
        departments=[
            DepartmentMeteoAlert(
                code="13",
                name="Bouches-du-Rhône",
                phenomena=[
                    PhenomenonAlert(
                        id="6", name="canicule", day1=Severity.ORANGE, day2=Severity.ROUGE
                    ),
                    PhenomenonAlert(
                        id="3", name="orages", day1=Severity.JAUNE, day2=Severity.VERT
                    ),
                ],
            ),
            DepartmentMeteoAlert(
                code="75",
                name="Paris",
                phenomena=[
                    PhenomenonAlert(
                        id="2", name="pluie-inondation", day1=Severity.JAUNE, day2=Severity.JAUNE
                    ),
                ],
            ),
        ],
        fetched_at=datetime(2026, 4, 30, 12, 0, tzinfo=UTC),
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Stub the meteo loader and reset the module-level cache between tests."""
    snapshot = _make_snapshot()

    async def fake_loader() -> MeteoSnapshot:
        return snapshot

    cache = alerts_module._meteo_cache
    monkeypatch.setattr(cache, "_loader", fake_loader)
    monkeypatch.setattr(cache, "_value", None)
    monkeypatch.setattr(cache, "_loaded_at", 0.0)

    with TestClient(app) as c:
        yield c


def test_get_meteo_returns_active_departments(client: TestClient) -> None:
    resp = client.get("/alerts/meteo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["active"] is True
    assert body["source"] == "meteofrance.vigilance"
    codes = [d["code"] for d in body["departments"]]
    assert codes == ["13", "75"]
    assert body["departments"][0] == {
        "code": "13",
        "name": "Bouches-du-Rhône",
        "phenomena": [
            {"id": "6", "name": "canicule", "day1": "orange", "day2": "rouge"},
            {"id": "3", "name": "orages", "day1": "jaune", "day2": "vert"},
        ],
    }


def test_get_meteo_when_no_active(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    quiet = _make_snapshot(active=False)

    async def quiet_loader() -> MeteoSnapshot:
        return quiet

    monkeypatch.setattr(alerts_module._meteo_cache, "_loader", quiet_loader)
    monkeypatch.setattr(alerts_module._meteo_cache, "_value", None)
    monkeypatch.setattr(alerts_module._meteo_cache, "_loaded_at", 0.0)

    resp = client.get("/alerts/meteo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["active"] is False
    assert body["departments"] == []


def test_sources_unhealthy_before_first_fetch(client: TestClient) -> None:
    resp = client.get("/sources")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "meteofrance.vigilance"
    assert body[0]["healthy"] is False
    assert body[0]["last_refresh"] is None


def test_sources_healthy_after_fetch(client: TestClient) -> None:
    assert client.get("/alerts/meteo").status_code == 200
    resp = client.get("/sources")
    body = resp.json()
    assert body[0]["healthy"] is True
    assert body[0]["last_refresh"] is not None


def test_upstream_error_returns_502(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_loader() -> MeteoSnapshot:
        raise UpstreamError("VIGILANCE_APP_ID is malformed")

    monkeypatch.setattr(alerts_module._meteo_cache, "_loader", failing_loader)
    monkeypatch.setattr(alerts_module._meteo_cache, "_value", None)
    monkeypatch.setattr(alerts_module._meteo_cache, "_loaded_at", 0.0)

    resp = client.get("/alerts/meteo")
    assert resp.status_code == 502
    assert "VIGILANCE_APP_ID" in resp.json()["detail"]


def test_cache_reuses_value_within_ttl(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}
    snapshot = _make_snapshot()

    async def counting_loader() -> MeteoSnapshot:
        calls["n"] += 1
        return snapshot

    monkeypatch.setattr(alerts_module._meteo_cache, "_loader", counting_loader)

    client.get("/alerts/meteo")
    client.get("/alerts/meteo")
    client.get("/alerts/meteo")

    assert calls["n"] == 1
