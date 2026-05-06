from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from pfat_api.cache import TTLCache
from pfat_api.config import settings
from pfat_api.schemas import ElectricitySnapshot, MeteoSnapshot, SourceMeta
from pfat_api.sources import rte
from pfat_api.sources.meteofrance import UpstreamError, fetch_meteo_snapshot

router = APIRouter()

_meteo_cache: TTLCache[MeteoSnapshot] = TTLCache(
    ttl_seconds=settings.cache_ttl_seconds,
    loader=fetch_meteo_snapshot,
)

# RTE Ecowatt is rate-limited to 1 request per 15 minutes per client_id;
# don't piggy-back on the meteo TTL which is much longer (1h by default).
RTE_CACHE_TTL_S = 900
_electricity_cache: TTLCache[ElectricitySnapshot] = TTLCache(
    ttl_seconds=RTE_CACHE_TTL_S,
    loader=rte.fetch_electricity_snapshot,
)


async def _load_snapshot() -> MeteoSnapshot:
    try:
        return await _meteo_cache.get()
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/alerts/meteo", response_model=MeteoSnapshot)
async def get_meteo_alerts() -> MeteoSnapshot:
    """Return all metropolitan departments with at least one phenomenon at jaune or above.

    A phenomenon is included only if its severity exceeds vert on day1 or day2. Source:
    Météo-France Vigilance (`meteole`).
    """
    return await _load_snapshot()


@router.get("/alerts/electricity", response_model=ElectricitySnapshot)
async def get_electricity_alerts() -> ElectricitySnapshot:
    """National electricity grid tension forecast (today + 3 days).

    Source: RTE Ecowatt v5. Cached server-side for 15 minutes (RTE rate-limits to
    1 request per 15 minutes). Returns 503 if RTE credentials are not configured.
    """
    try:
        return await _electricity_cache.get()
    except rte.CredentialsMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except rte.UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/sources", response_model=list[SourceMeta])
async def get_sources() -> list[SourceMeta]:
    loaded_at = _meteo_cache.loaded_at
    return [
        SourceMeta(
            name="meteofrance.vigilance",
            last_refresh=datetime.fromtimestamp(loaded_at, tz=UTC) if loaded_at else None,
            healthy=loaded_at > 0,
        )
    ]
