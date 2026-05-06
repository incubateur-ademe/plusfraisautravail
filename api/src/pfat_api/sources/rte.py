"""RTE Ecowatt v5 — national electricity grid tension forecast.

Auth flow: OAuth2 client_credentials, Basic-auth on the token endpoint, JWT bearer
on the API. Token TTL is 2h; signals are rate-limited to 1 call / 15 min so the
caller is responsible for caching the result (we do that one level up via TTLCache).
"""
from __future__ import annotations

import asyncio
import base64
import logging
import threading
import time
from datetime import UTC, datetime

import httpx

from pfat_api.config import settings
from pfat_api.schemas import (
    ElectricityDayForecast,
    ElectricityLevel,
    ElectricitySnapshot,
)

logger = logging.getLogger(__name__)

TOKEN_URL = "https://digital.iservices.rte-france.com/token/oauth/"
SIGNALS_URL_PROD = "https://digital.iservices.rte-france.com/open_api/ecowatt/v5/signals"
SIGNALS_URL_SANDBOX = (
    "https://digital.iservices.rte-france.com/open_api/ecowatt/v5/sandbox/signals"
)

TOKEN_REQUEST_TIMEOUT_S = 15.0
SIGNALS_REQUEST_TIMEOUT_S = 30.0

# Per RTE docs, dvalue can be 1/2/3 on the day-level signal.
DVALUE_TO_LEVEL: dict[int, ElectricityLevel] = {
    1: ElectricityLevel.VERT,
    2: ElectricityLevel.ORANGE,
    3: ElectricityLevel.ROUGE,
}


class UpstreamError(RuntimeError):
    """Raised when the RTE API can't be reached or returns garbage."""


class CredentialsMissing(RuntimeError):
    """Raised when neither sandbox mode nor production creds are configured."""


class _TokenCache:
    """Thread-safe TTL cache for the RTE OAuth bearer token."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def get(self, client_id: str, client_secret: str) -> str:
        now = time.time()
        if self._token and self._expires_at > now + 30:
            return self._token
        with self._lock:
            now = time.time()
            if self._token and self._expires_at > now + 30:
                return self._token
            self._token, ttl = _request_token(client_id, client_secret)
            self._expires_at = now + ttl
            return self._token


_token_cache = _TokenCache()


def _request_token(client_id: str, client_secret: str) -> tuple[str, int]:
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    try:
        resp = httpx.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=TOKEN_REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        body = resp.json()
    except Exception as exc:
        logger.exception("RTE token request failed")
        raise UpstreamError(
            "Could not obtain a token from RTE. Check RTE_CLIENT_ID/RTE_CLIENT_SECRET "
            "and that the application is subscribed to Ecowatt v5."
        ) from exc
    token = body.get("access_token")
    ttl = int(body.get("expires_in", 7200))
    if not token:
        raise UpstreamError("RTE token endpoint returned no access_token.")
    return token, ttl


def _fetch_snapshot_sync() -> ElectricitySnapshot:
    """Synchronous fetch. Always Bearer-authenticated; URL switches between prod and sandbox.

    Sandbox returns canned data (useful when the v5 prod payload is all-vert) but still
    requires a valid OAuth token from the same RTE Data API account.
    """
    if not (settings.rte_client_id and settings.rte_client_secret):
        raise CredentialsMissing(
            "RTE Ecowatt is not configured. Set RTE_CLIENT_ID and RTE_CLIENT_SECRET. "
            "Both prod and sandbox endpoints require an OAuth token."
        )
    url = SIGNALS_URL_SANDBOX if settings.rte_use_sandbox else SIGNALS_URL_PROD
    signals = _fetch_signals(url, settings.rte_client_id, settings.rte_client_secret)
    return _parse_signals(signals)


def _fetch_signals(url: str, client_id: str, client_secret: str) -> list[dict]:
    token = _token_cache.get(client_id, client_secret)
    try:
        resp = httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=SIGNALS_REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        body = resp.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            logger.warning("RTE rate limit hit (429) — caller should cache more aggressively")
        logger.exception("RTE signals fetch failed")
        raise UpstreamError(
            f"RTE Ecowatt signals returned HTTP {exc.response.status_code}."
        ) from exc
    except Exception as exc:
        logger.exception("RTE signals fetch failed")
        raise UpstreamError("Could not fetch Ecowatt signals from RTE.") from exc
    return body.get("signals", [])


def _parse_signals(signals: list[dict]) -> ElectricitySnapshot:
    days: list[ElectricityDayForecast] = []
    for s in signals:
        # `jour` is ISO with timezone, e.g. "2026-05-06T00:00:00+02:00" — keep only the date.
        jour = str(s.get("jour", ""))[:10]
        dvalue = int(s.get("dvalue", 1))
        # dvalue 0 (carbon-free) only appears on hourly hvalue, not day-level; clamp defensively.
        level = DVALUE_TO_LEVEL.get(dvalue, ElectricityLevel.VERT)
        days.append(
            ElectricityDayForecast(
                date=jour,
                level=level,
                code=dvalue,
                message=s.get("message"),
            )
        )
    days.sort(key=lambda d: d.date)

    currently_strained = bool(days) and days[0].level != ElectricityLevel.VERT
    upcoming_strain = any(d.level != ElectricityLevel.VERT for d in days[1:])

    return ElectricitySnapshot(
        days=days,
        currently_strained=currently_strained,
        upcoming_strain=upcoming_strain,
        fetched_at=datetime.now(UTC),
    )


async def fetch_electricity_snapshot() -> ElectricitySnapshot:
    return await asyncio.to_thread(_fetch_snapshot_sync)
