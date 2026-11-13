"""Tests for the Climadiag search source + /climadiag/search route."""

from typing import Any

import httpx
import pytest
from pfat_api.sources import climadiag

pytestmark = pytest.mark.django_db


def _lieu(*, id: int = 1, nom: str = "Cadenet", type_lieu: str = "commune") -> dict[str, Any]:
    projection = {"min": 1.0, "median": 2.0, "max": 3.0}
    return {
        "id": id,
        "nom": nom,
        "code_postal": "84160",
        "type_lieu": type_lieu,
        "seuil_jours_tres_chauds": 35.0,
        "seuil_nuits_chaudes": 20.0,
        "jours_tres_chauds_ref": 5.0,
        "nuits_chaudes_ref": 3.0,
        "jours_vdc_ref": 1.0,
        "jours_tres_chauds_prevision": {
            "2030": projection,
            "2050": projection,
            "2100": projection,
        },
        "nuits_chaudes_prevision": {
            "2030": projection,
            "2050": projection,
            "2100": projection,
        },
        "jours_vdc_prevision": None,
    }


def test_search_missing_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(climadiag.settings, "climadiag_api_token", None)
    with pytest.raises(climadiag.CredentialsMissingError):
        climadiag.search_climadiag("84450")


def test_route_returns_503_when_token_missing(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(climadiag.settings, "climadiag_api_token", None)
    resp = client.get("/api/climadiag/search", {"search": "84450"})
    assert resp.status_code == 503


def test_route_returns_results(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(climadiag.settings, "climadiag_api_token", "test-token")

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        assert kwargs["headers"]["X-AUTH-TOKEN"] == "test-token"
        assert kwargs["params"] == {"search": "84450", "limit": 15}
        return httpx.Response(200, json=[_lieu()], request=httpx.Request("GET", url))

    monkeypatch.setattr(climadiag.httpx, "get", fake_get)

    resp = client.get("/api/climadiag/search", {"search": "84450"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["nom"] == "Cadenet"


def test_route_filters_epci_when_communes_only(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(climadiag.settings, "climadiag_api_token", "test-token")

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                _lieu(id=1, nom="Cadenet", type_lieu="commune"),
                _lieu(id=2, nom="CC Pays", type_lieu="epci"),
            ],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(climadiag.httpx, "get", fake_get)

    resp = client.get("/api/climadiag/search", {"search": "84", "communes_only": "true"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["type_lieu"] == "commune"


def test_limit_is_clamped(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(climadiag.settings, "climadiag_api_token", "test-token")

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        assert kwargs["params"]["limit"] == 20
        return httpx.Response(200, json=[], request=httpx.Request("GET", url))

    monkeypatch.setattr(climadiag.httpx, "get", fake_get)

    resp = client.get("/api/climadiag/search", {"search": "84", "limit": 20})
    assert resp.status_code == 200


def test_upstream_error_returns_502(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(climadiag.settings, "climadiag_api_token", "test-token")

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(climadiag.httpx, "get", fake_get)

    resp = client.get("/api/climadiag/search", {"search": "84"})
    assert resp.status_code == 502
