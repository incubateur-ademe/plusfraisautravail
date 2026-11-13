"""Upstream snapshots kept in a Django cache.

With a cache shared by every worker and instance (database, Redis), the upstream rate
limits hold across processes. The last snapshot is kept a day past its TTL and served
when the upstream fails, rather than a 502.
"""

import logging
import threading
import time
from collections.abc import Callable

from django.core.cache import caches

from pfat_api.config import settings

logger = logging.getLogger(__name__)

KEEP_STALE_S = 86_400


class SnapshotCache[T]:
    def __init__(
        self,
        key: str,
        ttl_seconds: int,
        loader: Callable[[], T],
        upstream_errors: tuple[type[Exception], ...],
    ) -> None:
        self.key = f"pfat_api:{key}"
        self.ttl = ttl_seconds
        self.loader = loader
        self.upstream_errors = upstream_errors
        # ponytail: per-process lock, so each worker may still refresh once; a cache lock
        # (Redis) if the upstream limits get tighter.
        self._lock = threading.Lock()

    def _entry(self) -> tuple[float, T] | None:
        return caches[settings.cache_alias].get(self.key)

    @property
    def loaded_at(self) -> float:
        entry = self._entry()
        return entry[0] if entry else 0.0

    def get(self) -> T:
        entry = self._entry()
        if entry and time.time() - entry[0] < self.ttl:
            return entry[1]
        with self._lock:
            entry = self._entry()
            if entry and time.time() - entry[0] < self.ttl:
                return entry[1]
            try:
                value = self.loader()
            except self.upstream_errors:
                if entry is None:
                    raise
                logger.warning("%s: upstream failed, serving the stale snapshot", self.key)
                return entry[1]
            caches[settings.cache_alias].set(self.key, (time.time(), value), KEEP_STALE_S)
            return value
