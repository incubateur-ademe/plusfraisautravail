from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from django.core.cache import caches
from pfat_api import api as api_module
from pfat_api.config import settings as api_settings
from pfat_api.schemas import (
    DepartmentMeteoAlert,
    MeteoSnapshot,
    PhenomenonAlert,
    Severity,
)
from pfat_api.sources.meteofrance import UpstreamError

pytestmark = pytest.mark.django_db


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
                    PhenomenonAlert(id="3", name="orages", day1=Severity.JAUNE, day2=Severity.VERT),
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


@pytest.fixture(autouse=True)
def empty_cache() -> Iterator[None]:
    caches[api_settings.cache_alias].clear()
    yield
    caches[api_settings.cache_alias].clear()


@pytest.fixture
def api_client(client, monkeypatch: pytest.MonkeyPatch):
    """Stub the meteo loader; the cache starts empty."""
    snapshot = _make_snapshot()
    monkeypatch.setattr(api_module.meteo_cache, "loader", lambda: snapshot)
    return client


def test_get_meteo_returns_active_departments(api_client) -> None:
    resp = api_client.get("/api/alerts/meteo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["active"] is True
    assert body["source"] == "meteofrance.vigilance"
    assert body["fetched_at"] == "2026-04-30T12:00:00Z"
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


def test_get_meteo_when_no_active(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    quiet = _make_snapshot(active=False)
    monkeypatch.setattr(api_module.meteo_cache, "loader", lambda: quiet)

    resp = api_client.get("/api/alerts/meteo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["active"] is False
    assert body["departments"] == []


def test_sources_unhealthy_before_first_fetch(api_client) -> None:
    resp = api_client.get("/api/sources")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "meteofrance.vigilance"
    assert body[0]["healthy"] is False
    assert body[0]["last_refresh"] is None


def test_sources_healthy_after_fetch(api_client) -> None:
    assert api_client.get("/api/alerts/meteo").status_code == 200
    resp = api_client.get("/api/sources")
    body = resp.json()
    assert body[0]["healthy"] is True
    assert body[0]["last_refresh"] is not None


def test_upstream_error_returns_502(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_loader() -> MeteoSnapshot:
        raise UpstreamError("VIGILANCE_APP_ID is malformed")

    monkeypatch.setattr(api_module.meteo_cache, "loader", failing_loader)

    resp = api_client.get("/api/alerts/meteo")
    assert resp.status_code == 502
    assert "VIGILANCE_APP_ID" in resp.json()["detail"]


def test_missing_vigilance_app_id_returns_503(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    from pfat_api.sources import meteofrance

    monkeypatch.setattr(api_module.meteo_cache, "loader", meteofrance.fetch_meteo_snapshot)
    monkeypatch.setattr(meteofrance.settings, "vigilance_app_id", None)

    resp = api_client.get("/api/alerts/meteo")
    assert resp.status_code == 503
    assert "VIGILANCE_APP_ID" in resp.json()["detail"]


def test_cache_reuses_value_within_ttl(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}
    snapshot = _make_snapshot()

    def counting_loader() -> MeteoSnapshot:
        calls["n"] += 1
        return snapshot

    monkeypatch.setattr(api_module.meteo_cache, "loader", counting_loader)

    api_client.get("/api/alerts/meteo")
    api_client.get("/api/alerts/meteo")
    api_client.get("/api/alerts/meteo")

    assert calls["n"] == 1


def test_stale_snapshot_is_served_when_the_upstream_fails(
    api_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert api_client.get("/api/alerts/meteo").status_code == 200
    monkeypatch.setattr(api_module.meteo_cache, "ttl", 0)

    def failing_loader() -> MeteoSnapshot:
        raise UpstreamError("Météo-France is down")

    monkeypatch.setattr(api_module.meteo_cache, "loader", failing_loader)

    resp = api_client.get("/api/alerts/meteo")
    assert resp.status_code == 200
    assert resp.json()["active"] is True
