"""The alert and Climadiag routes, mounted by the project under ``/api/``."""

from datetime import UTC, datetime

from ninja import NinjaAPI, Query
from ninja.errors import HttpError

from pfat_api.cache import SnapshotCache
from pfat_api.config import settings
from pfat_api.schemas import ClimadiagLieu, ElectricitySnapshot, MeteoSnapshot, SourceMeta
from pfat_api.sources import climadiag, meteofrance, rte

api = NinjaAPI(
    title="pfat-api",
    description="Alert sources aggregated for plusfraisautravail.beta.gouv.fr.",
    version="0.1.0",
    urls_namespace="pfat_api",
)

meteo_cache = SnapshotCache(
    "meteo",
    ttl_seconds=settings.cache_ttl_seconds,
    loader=meteofrance.fetch_meteo_snapshot,
    upstream_errors=(meteofrance.UpstreamError,),
)

# RTE Ecowatt is rate-limited to 1 request per 15 minutes per client_id;
# don't piggy-back on the meteo TTL which is much longer (1h by default).
RTE_CACHE_TTL_S = 900
electricity_cache = SnapshotCache(
    "electricity",
    ttl_seconds=RTE_CACHE_TTL_S,
    loader=rte.fetch_electricity_snapshot,
    upstream_errors=(rte.UpstreamError,),
)


@api.get("/alerts/meteo", response=MeteoSnapshot)
def get_meteo_alerts(request):
    """Return all metropolitan departments with at least one phenomenon at jaune or above.

    A phenomenon is included only if its severity exceeds vert on day1 or day2. Source:
    Météo-France Vigilance (`meteole`).
    """
    try:
        return meteo_cache.get()
    except meteofrance.CredentialsMissingError as exc:
        raise HttpError(503, str(exc)) from exc
    except meteofrance.UpstreamError as exc:
        raise HttpError(502, str(exc)) from exc


@api.get("/alerts/electricity", response=ElectricitySnapshot)
def get_electricity_alerts(request):
    """National electricity grid tension forecast (today + 3 days).

    Source: RTE Ecowatt v5. Cached server-side for 15 minutes (RTE rate-limits to
    1 request per 15 minutes). Returns 503 if RTE credentials are not configured.
    """
    try:
        return electricity_cache.get()
    except rte.CredentialsMissingError as exc:
        raise HttpError(503, str(exc)) from exc
    except rte.UpstreamError as exc:
        raise HttpError(502, str(exc)) from exc


@api.get("/sources", response=list[SourceMeta])
def get_sources(request):
    loaded_at = meteo_cache.loaded_at
    return [
        SourceMeta(
            name="meteofrance.vigilance",
            last_refresh=datetime.fromtimestamp(loaded_at, tz=UTC) if loaded_at else None,
            healthy=loaded_at > 0,
        )
    ]


@api.get("/climadiag/search", response=list[ClimadiagLieu])
def search_climadiag(
    request,
    search: str = Query(..., min_length=1),
    limit: int = Query(climadiag.DEFAULT_LIMIT, ge=climadiag.MIN_LIMIT, le=climadiag.MAX_LIMIT),
    communes_only: bool = Query(
        False, description="If true, filter out EPCI results (keep only type_lieu='commune')."
    ),
):
    """Search Climadiag data by postal code, INSEE code, or commune/EPCI name.

    Proxies plusfraichemaville.fr's Climadiag search so the token stays server-side.
    """
    try:
        results = climadiag.search_climadiag(search, limit)
    except climadiag.CredentialsMissingError as exc:
        raise HttpError(503, str(exc)) from exc
    except climadiag.UpstreamError as exc:
        raise HttpError(502, str(exc)) from exc

    if communes_only:
        results = [r for r in results if r.type_lieu == "commune"]
    return results
