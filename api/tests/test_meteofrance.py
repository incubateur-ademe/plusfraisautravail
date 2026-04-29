"""Source-level tests for the Météo-France adapter — padding + parsing."""

from typing import Any

import pytest

from pfat_api.schemas import Severity
from pfat_api.sources import meteofrance as mf


class FakeVigilance:
    """Minimal stub of meteole.Vigilance.get_phenomenon()."""

    def __init__(self, phenomenon_items_by_domain: dict[str, list[dict[str, Any]]]) -> None:
        self._items = phenomenon_items_by_domain

    def get_phenomenon(self) -> tuple[None, dict[str, list[Any]]]:
        df = {
            "domain_id": list(self._items.keys()),
            "phenomenon_items": list(self._items.values()),
        }
        return None, df


def _patch_vigilance(
    monkeypatch: pytest.MonkeyPatch,
    items: dict[str, list[dict[str, Any]]],
) -> None:
    monkeypatch.setattr(mf, "Vigilance", lambda application_id: FakeVigilance(items))


def test_returns_all_96_metropolitan_departments(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_vigilance(monkeypatch, {})
    snapshot = mf._fetch_heatwave_sync()
    assert len(snapshot.departments) == 96
    codes = [d.code for d in snapshot.departments]
    assert "75" in codes
    assert "2A" in codes
    assert "2B" in codes
    assert all(d.day1 == Severity.VERT and d.day2 == Severity.VERT for d in snapshot.departments)


def test_padded_departments_default_to_vert(monkeypatch: pytest.MonkeyPatch) -> None:
    # Upstream only reports for "06" — every other dept should still be present, all vert.
    _patch_vigilance(
        monkeypatch,
        {
            "06": [
                {"phenomenon_id": mf.HEATWAVE_PHENOMENON_ID, "phenomenon_max_color_id": 3},
                {"phenomenon_id": mf.HEATWAVE_PHENOMENON_ID, "phenomenon_max_color_id": 2},
            ],
        },
    )
    snapshot = mf._fetch_heatwave_sync()
    by_code = {d.code: d for d in snapshot.departments}
    assert by_code["06"].day1 == Severity.ORANGE
    assert by_code["06"].day2 == Severity.JAUNE
    assert by_code["75"].day1 == Severity.VERT
    assert by_code["75"].day2 == Severity.VERT


def test_non_heatwave_phenomena_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_vigilance(
        monkeypatch,
        {
            "75": [
                # phenomenon "3" = pluie-inondation, must be ignored
                {"phenomenon_id": "3", "phenomenon_max_color_id": 4},
                # phenomenon "8" = canicule, the one we care about
                {"phenomenon_id": mf.HEATWAVE_PHENOMENON_ID, "phenomenon_max_color_id": 2},
            ],
        },
    )
    snapshot = mf._fetch_heatwave_sync()
    by_code = {d.code: d for d in snapshot.departments}
    assert by_code["75"].day1 == Severity.JAUNE


def test_upstream_error_wraps_meteole_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(application_id: str) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(mf, "Vigilance", boom)
    with pytest.raises(mf.UpstreamError):
        mf._fetch_heatwave_sync()
