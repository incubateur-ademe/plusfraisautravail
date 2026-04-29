from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from pfat_api.cache import TTLCache
from pfat_api.config import settings
from pfat_api.schemas import HeatwaveSnapshot, SourceMeta
from pfat_api.sources.meteofrance import UpstreamError, fetch_heatwave

router = APIRouter()

_heatwave_cache: TTLCache[HeatwaveSnapshot] = TTLCache(
    ttl_seconds=settings.cache_ttl_seconds,
    loader=fetch_heatwave,
)


async def _load_heatwave() -> HeatwaveSnapshot:
    try:
        return await _heatwave_cache.get()
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/alerts/heatwave", response_model=HeatwaveSnapshot)
async def get_heatwave() -> HeatwaveSnapshot:
    return await _load_heatwave()


@router.get("/alerts/heatwave/{dept}", response_model=HeatwaveSnapshot)
async def get_heatwave_for_department(dept: str) -> HeatwaveSnapshot:
    snapshot = await _load_heatwave()
    code = dept.upper()
    matching = [d for d in snapshot.departments if d.code == code]
    if not matching:
        raise HTTPException(status_code=404, detail=f"No data for department '{code}'.")
    return HeatwaveSnapshot(
        phenomenon=snapshot.phenomenon,
        phenomenon_id=snapshot.phenomenon_id,
        departments=matching,
        fetched_at=snapshot.fetched_at,
        source=snapshot.source,
    )


@router.get("/sources", response_model=list[SourceMeta])
async def get_sources() -> list[SourceMeta]:
    loaded_at = _heatwave_cache.loaded_at
    return [
        SourceMeta(
            name="meteofrance.vigilance",
            last_refresh=datetime.fromtimestamp(loaded_at, tz=UTC) if loaded_at else None,
            healthy=loaded_at > 0,
        )
    ]
