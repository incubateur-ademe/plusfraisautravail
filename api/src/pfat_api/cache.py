import asyncio
import time
from collections.abc import Awaitable, Callable


class TTLCache[T]:
    """Single-value async TTL cache. Coalesces concurrent refreshes via a lock."""

    def __init__(self, ttl_seconds: int, loader: Callable[[], Awaitable[T]]) -> None:
        self._ttl = ttl_seconds
        self._loader = loader
        self._value: T | None = None
        self._loaded_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def loaded_at(self) -> float:
        return self._loaded_at

    async def get(self) -> T:
        if self._value is not None and (time.time() - self._loaded_at) < self._ttl:
            return self._value
        async with self._lock:
            if self._value is not None and (time.time() - self._loaded_at) < self._ttl:
                return self._value
            self._value = await self._loader()
            self._loaded_at = time.time()
            return self._value
