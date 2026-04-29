import asyncio
import logging
from datetime import UTC, datetime

from meteole import Vigilance

from pfat_api.config import settings
from pfat_api.schemas import COLOR_ID_TO_SEVERITY, DepartmentAlert, HeatwaveSnapshot

logger = logging.getLogger(__name__)

HEATWAVE_PHENOMENON_ID = "8"

# Metropolitan departments (96 codes incl. Corsica 2A/2B).
# The Vigilance API only returns entries for departments where the phenomenon
# is actively monitored — anything missing defaults to "vert".
METROPOLITAN_DEPARTMENTS: tuple[str, ...] = (
    "01", "02", "03", "04", "05", "06", "07", "08", "09",
    "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "2A", "2B",
    "21", "22", "23", "24", "25", "26", "27", "28", "29",
    "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "43", "44", "45", "46", "47", "48", "49",
    "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "60", "61", "62", "63", "64", "65", "66", "67", "68", "69",
    "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
    "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
    "90", "91", "92", "93", "94", "95",
)


class UpstreamError(RuntimeError):
    """Raised when the upstream Météo-France API can't be reached or returns garbage."""


def _fetch_heatwave_sync() -> HeatwaveSnapshot:
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

    by_dept: dict[str, list[int]] = {}
    domains = df_timelaps["domain_id"]
    phenomenon_items = df_timelaps["phenomenon_items"]
    for domain, items in zip(domains, phenomenon_items, strict=True):
        for phenomenon in items:
            if phenomenon["phenomenon_id"] != HEATWAVE_PHENOMENON_ID:
                continue
            by_dept.setdefault(str(domain), []).append(int(phenomenon["phenomenon_max_color_id"]))

    vert = COLOR_ID_TO_SEVERITY[1]
    departments: list[DepartmentAlert] = []
    for code in METROPOLITAN_DEPARTMENTS:
        colors = by_dept.get(code, [])
        day1 = COLOR_ID_TO_SEVERITY[colors[0]] if len(colors) > 0 else vert
        day2 = COLOR_ID_TO_SEVERITY[colors[1]] if len(colors) > 1 else day1
        departments.append(DepartmentAlert(code=code, day1=day1, day2=day2))

    return HeatwaveSnapshot(
        departments=departments,
        fetched_at=datetime.now(UTC),
    )


async def fetch_heatwave() -> HeatwaveSnapshot:
    return await asyncio.to_thread(_fetch_heatwave_sync)
