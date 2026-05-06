"""Source-level tests for the Météo-France adapter."""

from typing import Any

import pytest

from pfat_api.schemas import Severity
from pfat_api.sources import meteofrance as mf


class _FakeRow(dict[str, Any]):
    """dict that accepts pandas-style row indexing (`row["domain_id"]`)."""


class FakeDataframe:
    """Minimal stub of pandas.DataFrame supporting iterrows() over a list of rows."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = [_FakeRow(r) for r in rows]

    def iterrows(self) -> Any:
        for i, r in enumerate(self._rows):
            yield i, r


class FakeVigilance:
    """Minimal stub of meteole.Vigilance.get_phenomenon()."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def get_phenomenon(self) -> tuple[None, FakeDataframe]:
        return None, FakeDataframe(self._rows)


def _patch_vigilance(
    monkeypatch: pytest.MonkeyPatch,
    rows: list[dict[str, Any]],
) -> None:
    monkeypatch.setattr(mf, "Vigilance", lambda application_id: FakeVigilance(rows))


def test_no_active_phenomena_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_vigilance(monkeypatch, [])
    snapshot = mf._fetch_snapshot_sync()
    assert snapshot.active is False
    assert snapshot.departments == []


def test_active_phenomenon_promotes_dept(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_vigilance(
        monkeypatch,
        [
            {
                "domain_id": "06",
                "echeance": "J",
                "phenomenon_items": [
                    {"phenomenon_id": "6", "phenomenon_max_color_id": 3},
                ],
            },
            {
                "domain_id": "06",
                "echeance": "J1",
                "phenomenon_items": [
                    {"phenomenon_id": "6", "phenomenon_max_color_id": 2},
                ],
            },
        ],
    )
    snapshot = mf._fetch_snapshot_sync()
    assert snapshot.active is True
    assert len(snapshot.departments) == 1
    dept = snapshot.departments[0]
    assert dept.code == "06"
    assert dept.name == "Alpes-Maritimes"
    assert len(dept.phenomena) == 1
    p = dept.phenomena[0]
    assert p.id == "6"
    assert p.name == "canicule"
    assert p.day1 == Severity.ORANGE
    assert p.day2 == Severity.JAUNE


def test_vert_only_phenomenon_is_filtered_out(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_vigilance(
        monkeypatch,
        [
            {
                "domain_id": "75",
                "echeance": "J",
                "phenomenon_items": [
                    {"phenomenon_id": "1", "phenomenon_max_color_id": 1},
                    {"phenomenon_id": "6", "phenomenon_max_color_id": 1},
                ],
            },
        ],
    )
    snapshot = mf._fetch_snapshot_sync()
    assert snapshot.active is False
    assert snapshot.departments == []


def test_multiple_phenomena_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_vigilance(
        monkeypatch,
        [
            {
                "domain_id": "13",
                "echeance": "J",
                "phenomenon_items": [
                    {"phenomenon_id": "3", "phenomenon_max_color_id": 2},
                    {"phenomenon_id": "6", "phenomenon_max_color_id": 3},
                    {"phenomenon_id": "1", "phenomenon_max_color_id": 1},
                ],
            },
            {
                "domain_id": "13",
                "echeance": "J1",
                "phenomenon_items": [
                    {"phenomenon_id": "3", "phenomenon_max_color_id": 1},
                    {"phenomenon_id": "6", "phenomenon_max_color_id": 4},
                ],
            },
        ],
    )
    snapshot = mf._fetch_snapshot_sync()
    by_code = {d.code: d for d in snapshot.departments}
    p_by_id = {p.id: p for p in by_code["13"].phenomena}

    # storm: jaune today, vert tomorrow → kept
    assert p_by_id["3"].day1 == Severity.JAUNE
    assert p_by_id["3"].day2 == Severity.VERT
    # canicule: orange → rouge
    assert p_by_id["6"].day1 == Severity.ORANGE
    assert p_by_id["6"].day2 == Severity.ROUGE
    # wind stayed vert both days → dropped
    assert "1" not in p_by_id


def test_non_metropolitan_domains_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_vigilance(
        monkeypatch,
        [
            {
                "domain_id": "FRA",
                "echeance": "J",
                "phenomenon_items": [
                    {"phenomenon_id": "6", "phenomenon_max_color_id": 4},
                ],
            },
            {
                "domain_id": "3010",
                "echeance": "J",
                "phenomenon_items": [
                    {"phenomenon_id": "3", "phenomenon_max_color_id": 3},
                ],
            },
            {
                "domain_id": "99",
                "echeance": "J",
                "phenomenon_items": [
                    {"phenomenon_id": "3", "phenomenon_max_color_id": 2},
                ],
            },
        ],
    )
    snapshot = mf._fetch_snapshot_sync()
    assert snapshot.active is False
    assert snapshot.departments == []


def test_upstream_error_wraps_meteole_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(application_id: str) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(mf, "Vigilance", boom)
    with pytest.raises(mf.UpstreamError):
        mf._fetch_snapshot_sync()
