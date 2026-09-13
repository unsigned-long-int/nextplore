import time
from collections import OrderedDict
from typing import Generic, TypeVar

T = TypeVar("T")


class LocalTTLCache(Generic[T]):
    def __init__(self, ttl_secs: int = 600, maxsize: int = 1024) -> None:
        self.ttl_secs = ttl_secs
        self._maxsize = maxsize
        self._store: OrderedDict[str, tuple[T, float]] = OrderedDict()

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: T) -> None:
        if key not in self._store and len(self._store) >= self._maxsize:
            self._store.popitem(last=False)
        self._store[key] = (value, time.monotonic() + self.ttl_secs)

    def delete_prefix(self, prefix: str) -> None:
        for key in [k for k in self._store if k.startswith(prefix)]:
            del self._store[key]
