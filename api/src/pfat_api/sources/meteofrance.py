import asyncio
import logging
from datetime import UTC, datetime

from meteole import Vigilance

from pfat_api.config import settings
from pfat_api.departments import DEPARTMENT_NAMES
from pfat_api.schemas import (
    COLOR_ID_TO_SEVERITY,
    DepartmentMeteoAlert,
    MeteoSnapshot,
    PhenomenonAlert,
    Severity,
)

logger = logging.getLogger(__name__)

# Météo-France Vigilance phenomenon IDs.
# See `meteole.Vigilance.PHENOMENO_IDS` for the canonical English mapping.
PHENOMENON_NAMES: dict[str, str] = {
    "1": "vent",
    "2": "pluie-inondation",
    "3": "orages",
    "4": "inondation",
    "5": "neige-verglas",
    "6": "canicule",
    "7": "grand-froid",
    "8": "avalanches",
    "9": "vagues-submersion",
}

# Echeance values returned by meteole — "J" is today, "J1" is tomorrow.
ECHEANCE_DAY1 = "J"
ECHEANCE_DAY2 = "J1"


class UpstreamError(RuntimeError):
    """Raised when the upstream Météo-France API can't be reached or returns garbage."""


def _fetch_snapshot_sync() -> MeteoSnapshot:
    """Synchronous fetch — runs in a worker thread to avoid blocking the event loop."""
    try:
        vigi = Vigilance(application_id=settings.vigilance_app_id)
        _, df_timelaps = vigi.get_phenomenon()
    except Exception as exc:
        logger.exception("Météo-France Vigilance upstream call failed")
        raise UpstreamError(
            "Could not fetch data from Météo-France Vigilance. "
            "This usually means VIGILANCE_APP_ID is missing, malformed, "
            "or the application is not subscribed to the 'Données Vigilance' product."
        ) from exc

    # Index per-day phenomenon colors keyed by (dept_code, echeance).
    # Each row in df_timelaps is a single (domain, day) snapshot whose
    # `phenomenon_items` is a list of {phenomenon_id, phenomenon_max_color_id, ...}.
    by_dept_day: dict[tuple[str, str], dict[str, int]] = {}
    for _, row in df_timelaps.iterrows():
        code = str(row["domain_id"])
        if code not in DEPARTMENT_NAMES:
            continue  # skip national / coastal sub-zones
        echeance = str(row["echeance"])
        per_phenom: dict[str, int] = {}
        for item in row["phenomenon_items"]:
            per_phenom[str(item["phenomenon_id"])] = int(item["phenomenon_max_color_id"])
        by_dept_day[code, echeance] = per_phenom

    departments: list[DepartmentMeteoAlert] = []
    any_active = False
    for code in sorted(DEPARTMENT_NAMES):
        day1 = by_dept_day.get((code, ECHEANCE_DAY1), {})
        day2 = by_dept_day.get((code, ECHEANCE_DAY2), {})
        phenom_ids = sorted(set(day1) | set(day2), key=int)

        active_phenomena: list[PhenomenonAlert] = []
        for pid in phenom_ids:
            c1 = day1.get(pid, 1)
            c2 = day2.get(pid, 1)
            if c1 <= 1 and c2 <= 1:
                continue
            active_phenomena.append(
                PhenomenonAlert(
                    id=pid,
                    name=PHENOMENON_NAMES.get(pid, pid),
                    day1=COLOR_ID_TO_SEVERITY.get(c1, Severity.VERT),
                    day2=COLOR_ID_TO_SEVERITY.get(c2, Severity.VERT),
                )
            )

        if active_phenomena:
            any_active = True
            departments.append(
                DepartmentMeteoAlert(
                    code=code,
                    name=DEPARTMENT_NAMES[code],
                    phenomena=active_phenomena,
                )
            )

    return MeteoSnapshot(
        active=any_active,
        departments=departments,
        fetched_at=datetime.now(UTC),
    )


async def fetch_meteo_snapshot() -> MeteoSnapshot:
    return await asyncio.to_thread(_fetch_snapshot_sync)
