import threading
import time
from collections import OrderedDict
from typing import Optional, Tuple, TypeAlias
from sqlalchemy.engine import Engine

from nextplore_sdk.database.connection_maker.engine.engine_build import build_engine
from nextplore_sdk.database.connection_maker.models.connection_profile import ConnectionProfile


EngineSpecs: TypeAlias = Tuple[Engine, float]


class EngineManager:
    def __init__(
        self,
        maxsize: int = 256,
        idle_ttl: Optional[int] = 30 * 60
    ) -> None:
        self._maxsize = maxsize
        self._idle_ttl = idle_ttl
        self._lock = threading.RLock()
        self._engines: OrderedDict[ConnectionProfile, EngineSpecs] = OrderedDict()

    async def acquire_engine(self, profile: ConnectionProfile) -> Engine:
        now = time.monotonic()
        with self._lock:
            self._prune_locked(now)

            spec = self._engines.pop(profile, None)
            if spec is not None:
                engine, _ = spec
                self._engines[profile] = (engine, now)
                return engine

            if len(self._engines) >= self._maxsize:
                _, (old_engine, _) = self._engines.popitem(last=False)
                old_engine.dispose()

            engine = await build_engine(profile)
            self._engines[profile] = (engine, now)
            return engine

    def _prune_locked(self, now: Optional[float] = None) -> None:
        if self._idle_ttl is None:
            return
        if now is None:
            now = time.monotonic()

        to_evict = [key for key, (_, last_used) in self._engines.items() if now - last_used > self._idle_ttl]
        for key in to_evict:
            engine, _ = self._engines.pop(key)
            engine.dispose()

    def shutdown(self) -> None:
        with self._lock:
            items = list(self._engines.values())
            self._engines.clear()
        for engine, _ in items:
            engine.dispose()
