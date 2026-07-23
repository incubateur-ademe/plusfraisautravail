from fastapi import APIRouter, HTTPException, Query

from pfat_api.schemas import ClimadiagLieu
from pfat_api.sources import climadiag

router = APIRouter()


@router.get("/climadiag/search", response_model=list[ClimadiagLieu])
async def search_climadiag(
    search: str = Query(..., min_length=1),
    limit: int = Query(climadiag.DEFAULT_LIMIT, ge=climadiag.MIN_LIMIT, le=climadiag.MAX_LIMIT),
    communes_only: bool = Query(
        False, description="If true, filter out EPCI results (keep only type_lieu='commune')."
    ),
) -> list[ClimadiagLieu]:
    """Search Climadiag data by postal code, INSEE code, or commune/EPCI name.

    Proxies plusfraichemaville.fr's Climadiag search so the token stays server-side.
    """
    try:
        results = await climadiag.search_climadiag(search, limit)
    except climadiag.CredentialsMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except climadiag.UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if communes_only:
        results = [r for r in results if r.type_lieu == "commune"]
    return results
