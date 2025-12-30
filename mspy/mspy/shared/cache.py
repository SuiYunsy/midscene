from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    value: Any
    expire_at: Optional[float]

    def expired(self) -> bool:
        return self.expire_at is not None and time.time() > self.expire_at


class InMemoryCache:
    """
    简易内存缓存，满足 Agent 上下文缓存需求（不引入复杂依赖）。
    """

    def __init__(self) -> None:
        self._store: Dict[str, CacheEntry] = {}

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        if ttl_seconds is not None and ttl_seconds < 0:
            raise ValueError("ttl_seconds must be greater than or equal to 0")
        expire_at = time.time() + ttl_seconds if ttl_seconds else None
        self._store[key] = CacheEntry(value=value, expire_at=expire_at)

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.expired():
            del self._store[key]
            return None
        return entry.value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
