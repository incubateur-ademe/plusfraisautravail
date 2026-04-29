import asyncio
from datetime import UTC, datetime

from meteole import Vigilance

from pfat_api.config import settings
from pfat_api.schemas import COLOR_ID_TO_SEVERITY, DepartmentAlert, HeatwaveSnapshot

HEATWAVE_PHENOMENON_ID = "8"


def _fetch_heatwave_sync() -> HeatwaveSnapshot:
    """Synchronous fetch — runs in a worker thread to avoid blocking the event loop."""
    vigi = Vigilance(application_id=settings.vigilance_app_id)
    _, df_timelaps = vigi.get_phenomenon()

    by_dept: dict[str, list[int]] = {}
    domains = df_timelaps["domain_id"]
    phenomenon_items = df_timelaps["phenomenon_items"]
    for domain, items in zip(domains, phenomenon_items, strict=True):
        for phenomenon in items:
            if phenomenon["phenomenon_id"] != HEATWAVE_PHENOMENON_ID:
                continue
            by_dept.setdefault(str(domain), []).append(int(phenomenon["phenomenon_max_color_id"]))

    departments: list[DepartmentAlert] = []
    for code, colors in by_dept.items():
        day1 = COLOR_ID_TO_SEVERITY[colors[0]] if len(colors) > 0 else COLOR_ID_TO_SEVERITY[1]
        day2 = COLOR_ID_TO_SEVERITY[colors[1]] if len(colors) > 1 else day1
        departments.append(DepartmentAlert(code=code, day1=day1, day2=day2))

    return HeatwaveSnapshot(
        departments=sorted(departments, key=lambda d: d.code),
        fetched_at=datetime.now(UTC),
    )


async def fetch_heatwave() -> HeatwaveSnapshot:
    return await asyncio.to_thread(_fetch_heatwave_sync)
