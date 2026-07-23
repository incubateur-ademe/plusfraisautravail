"""PlusFraîcheMaVille Climadiag commune-search API.

Simple auth-token-forwarding proxy: search is free-text (postal code, INSEE code,
or commune/EPCI name), results are passed through as-is (already shaped like our
`ClimadiagLieu` schema). No caching - this is a live search, not a snapshot.
"""

from __future__ import annotations

import logging

import httpx

from pfat_api.config import settings
from pfat_api.schemas import ClimadiagLieu

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_S = 15.0
MIN_LIMIT = 0
MAX_LIMIT = 20
DEFAULT_LIMIT = 15


class UpstreamError(RuntimeError):
    """Raised when the PFMV Climadiag API can't be reached or returns garbage."""


class CredentialsMissingError(RuntimeError):
    """Raised when CLIMADIAG_API_TOKEN is not configured."""


async def search_climadiag(search: str, limit: int = DEFAULT_LIMIT) -> list[ClimadiagLieu]:
    if not settings.climadiag_api_token:
        raise CredentialsMissingError(
            "Climadiag search is not configured. Set CLIMADIAG_API_TOKEN."
        )
    clamped_limit = max(MIN_LIMIT, min(MAX_LIMIT, limit))
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
            resp = await client.get(
                settings.climadiag_api_url,
                headers={"X-AUTH-TOKEN": settings.climadiag_api_token},
                params={"search": search, "limit": clamped_limit},
            )
            resp.raise_for_status()
            body = resp.json()
    except Exception as exc:
        logger.exception("PFMV Climadiag search failed")
        raise UpstreamError("Could not fetch data from the Climadiag search API.") from exc

    results = body if isinstance(body, list) else body.get("results", [])
    return [ClimadiagLieu.model_validate(r) for r in results]
