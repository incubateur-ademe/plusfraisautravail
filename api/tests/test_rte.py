"""Tests for the RTE Ecowatt source + /alerts/electricity route."""
from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from pfat_api.main import app
from pfat_api.routes import alerts as alerts_module
from pfat_api.schemas import ElectricityLevel
from pfat_api.sources import rte


def _signals_payload(*levels: int) -> dict[str, Any]:
    """Build a fake RTE signals body with the given dvalues, dated d0..d3."""
    dates = [
        "2026-05-06T00:00:00+02:00",
        "2026-05-07T00:00:00+02:00",
        "2026-05-08T00:00:00+02:00",
        "2026-05-09T00:00:00+02:00",
    ]
    return {
        "signals": [
            {
                "GenerationFichier": "2026-05-06T07:00:00+02:00",
                "jour": dates[i],
                "dvalue": dv,
                "message": f"day {i}",
                "values": [],
            }
            for i, dv in enumerate(levels)
        ]
    }


class _FakeResponse:
    def __init__(self, status: int, body: Any) -> None:
        self.status_code = status
        self._body = body

    def json(self) -> Any:
        return self._body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=httpx.Request("GET", "https://example.test"),
                response=httpx.Response(self.status_code),
            )


def _stub_http(
    monkeypatch: pytest.MonkeyPatch,
    *,
    token_resp: _FakeResponse | None = None,
    signals_resp: _FakeResponse | None = None,
) -> dict[str, list[Any]]:
    """Patch httpx.post/get used inside pfat_api.sources.rte. Returns call log."""
    calls: dict[str, list[Any]] = {"post": [], "get": []}

    def fake_post(url: str, **kwargs: Any) -> _FakeResponse:
        calls["post"].append((url, kwargs))
        if token_resp is None:
            raise AssertionError("Unexpected POST")
        return token_resp

    def fake_get(url: str, **kwargs: Any) -> _FakeResponse:
        calls["get"].append((url, kwargs))
        if signals_resp is None:
            raise AssertionError("Unexpected GET")
        return signals_resp

    monkeypatch.setattr(rte.httpx, "post", fake_post)
    monkeypatch.setattr(rte.httpx, "get", fake_get)
    # Reset the module-level token cache between tests.
    rte._token_cache = rte._TokenCache()
    return calls


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    cache = alerts_module._electricity_cache
    monkeypatch.setattr(cache, "_value", None)
    monkeypatch.setattr(cache, "_loaded_at", 0.0)
    with TestClient(app) as c:
        yield c


def test_parse_signals_maps_levels_correctly() -> None:
    snapshot = rte._parse_signals(_signals_payload(1, 2, 3, 1)["signals"])
    assert [d.level for d in snapshot.days] == [
        ElectricityLevel.VERT,
        ElectricityLevel.ORANGE,
        ElectricityLevel.ROUGE,
        ElectricityLevel.VERT,
    ]
    assert [d.code for d in snapshot.days] == [1, 2, 3, 1]
    assert snapshot.days[0].date == "2026-05-06"


def test_currently_strained_today_orange() -> None:
    snapshot = rte._parse_signals(_signals_payload(2, 1, 1, 1)["signals"])
    assert snapshot.currently_strained is True
    assert snapshot.upcoming_strain is False


def test_upcoming_strain_only() -> None:
    snapshot = rte._parse_signals(_signals_payload(1, 1, 3, 1)["signals"])
    assert snapshot.currently_strained is False
    assert snapshot.upcoming_strain is True


def test_all_vert_means_neither_flag() -> None:
    snapshot = rte._parse_signals(_signals_payload(1, 1, 1, 1)["signals"])
    assert snapshot.currently_strained is False
    assert snapshot.upcoming_strain is False


def test_unknown_dvalue_clamped_to_vert() -> None:
    snapshot = rte._parse_signals(_signals_payload(0, 9, 1, 1)["signals"])
    assert snapshot.days[0].level == ElectricityLevel.VERT
    assert snapshot.days[1].level == ElectricityLevel.VERT


def test_token_is_cached_across_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rte.settings, "rte_use_sandbox", False)
    monkeypatch.setattr(rte.settings, "rte_client_id", "id")
    monkeypatch.setattr(rte.settings, "rte_client_secret", "secret")
    calls = _stub_http(
        monkeypatch,
        token_resp=_FakeResponse(200, {"access_token": "tok-1", "expires_in": 7200}),
        signals_resp=_FakeResponse(200, _signals_payload(1, 1, 1, 1)),
    )
    rte._fetch_snapshot_sync()
    rte._fetch_snapshot_sync()
    rte._fetch_snapshot_sync()
    assert len(calls["post"]) == 1, "token endpoint should only be hit once"
    assert len(calls["get"]) == 3


def test_sandbox_uses_sandbox_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rte.settings, "rte_use_sandbox", True)
    monkeypatch.setattr(rte.settings, "rte_client_id", "id")
    monkeypatch.setattr(rte.settings, "rte_client_secret", "secret")
    calls = _stub_http(
        monkeypatch,
        token_resp=_FakeResponse(200, {"access_token": "tok-1", "expires_in": 7200}),
        signals_resp=_FakeResponse(200, _signals_payload(1, 2, 1, 1)),
    )
    snapshot = rte._fetch_snapshot_sync()
    assert calls["get"][0][0] == rte.SIGNALS_URL_SANDBOX
    assert snapshot.days[1].level == ElectricityLevel.ORANGE


def test_missing_credentials_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rte.settings, "rte_use_sandbox", False)
    monkeypatch.setattr(rte.settings, "rte_client_id", None)
    monkeypatch.setattr(rte.settings, "rte_client_secret", None)
    with pytest.raises(rte.CredentialsMissing):
        rte._fetch_snapshot_sync()


def test_missing_credentials_raises_even_in_sandbox_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rte.settings, "rte_use_sandbox", True)
    monkeypatch.setattr(rte.settings, "rte_client_id", None)
    monkeypatch.setattr(rte.settings, "rte_client_secret", None)
    with pytest.raises(rte.CredentialsMissing):
        rte._fetch_snapshot_sync()


def test_token_endpoint_failure_wraps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rte.settings, "rte_use_sandbox", False)
    monkeypatch.setattr(rte.settings, "rte_client_id", "id")
    monkeypatch.setattr(rte.settings, "rte_client_secret", "secret")
    _stub_http(
        monkeypatch,
        token_resp=_FakeResponse(401, {"error": "invalid_client"}),
    )
    with pytest.raises(rte.UpstreamError):
        rte._fetch_snapshot_sync()


def test_route_returns_503_when_credentials_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def boom() -> Any:
        raise rte.CredentialsMissing("no creds")

    monkeypatch.setattr(alerts_module._electricity_cache, "_loader", boom)
    resp = client.get("/alerts/electricity")
    assert resp.status_code == 503
    assert "no creds" in resp.json()["detail"]


def test_route_returns_502_on_upstream_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def boom() -> Any:
        raise rte.UpstreamError("RTE down")

    monkeypatch.setattr(alerts_module._electricity_cache, "_loader", boom)
    resp = client.get("/alerts/electricity")
    assert resp.status_code == 502
    assert "RTE down" in resp.json()["detail"]


def test_route_returns_snapshot(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot = rte._parse_signals(_signals_payload(1, 2, 1, 1)["signals"])

    async def loader() -> Any:
        return snapshot

    monkeypatch.setattr(alerts_module._electricity_cache, "_loader", loader)

    resp = client.get("/alerts/electricity")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "rte.ecowatt"
    assert len(body["days"]) == 4
    assert body["currently_strained"] is False
    assert body["upcoming_strain"] is True
    assert body["days"][1]["level"] == "orange"
