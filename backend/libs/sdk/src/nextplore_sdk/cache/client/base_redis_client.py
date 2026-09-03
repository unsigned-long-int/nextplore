import json
import logging
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.json import pydantic_encoder
from redis.asyncio import Redis

from .interface import Cache
from .redis_client_factory import get_redis_client

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class BaseCache(Cache):
    def __init__(
        self,
        namespace: str,
        default_ttl: int = 600,
        redis: Redis | None = None,
        version: str | None = None,
    ):
        self.redis = redis or get_redis_client()
        self.prefix = f"{namespace}:{version}:" if version else f"{namespace}:"
        self.default_ttl = default_ttl

    def _key(self, *parts: str | UUID) -> str:
        return self.prefix + ":".join(str(part) for part in parts)

    async def get_one(self, *parts: str | UUID, model: type[T]) -> T | None:
        key = self._key(*parts)
        try:
            cached = await self.redis.get(key)
            if not cached:
                logger.info(f"Cache MISS {key}")
                return None

            obj = model.model_validate_json(cached)
            logger.info(f"Cache HIT {key}")
            return obj
        except (ValidationError, json.JSONDecodeError) as e:
            logger.warning(f"Cache INVALID DATA {key}: {e}")
            await self.redis.delete(key)
            return None
        except Exception as e:
            logger.error(f"Cache ERROR get({key}): {e}", exc_info=True)
            return None

    async def set_one(
        self, *parts: str | UUID, value: BaseModel, ttl: int | None = None
    ):
        key = self._key(*parts)
        try:
            payload = value.model_dump_json()
            await self.redis.set(key, value=payload, ex=ttl or self.default_ttl)
            logger.info(f"Cache SET {key}")
        except Exception as e:
            logger.error(f"Cache ERROR set({key}): {e}", exc_info=True)

    async def get_many(self, *parts: str | UUID, model: type[T]) -> list[T] | None:
        key = self._key(*parts)
        try:
            cached = await self.redis.get(key)
            if not cached:
                logger.info(f"Cache MISS: {key}")
                return None

            parsed = json.loads(cached)
            result = TypeAdapter(list[model]).validate_python(parsed)
            logger.info(f"Cache HIT {key}")
            return result
        except (ValidationError, json.JSONDecodeError) as ve:
            logger.warning(f"Cache INVALID LIST DATA {key}: {ve}")
            await self.redis.delete(key)
            return []
        except Exception as e:
            logger.error(f"Cache ERROR get_many({key}): {e}", exc_info=True)
            return []

    async def set_many(
        self, *parts: str | UUID, value: list[BaseModel], ttl: int | None = None
    ):
        key = self._key(*parts)
        try:
            payload = json.dumps(value, default=pydantic_encoder)
            await self.redis.set(key, value=payload, ex=ttl or self.default_ttl)
            logger.info(f"Cache SET LIST {key}")
        except Exception as e:
            logger.error(f"Cache ERROR set_many({key}): {e}", exc_info=True)

    async def get_raw(self, *parts: str | UUID) -> dict[str, Any] | None:
        key = self._key(*parts)
        try:
            cached = await self.redis.get(key)
            if not cached:
                logger.info(f"RAW Cache MISS {key}")
                return None
            obj = json.loads(cached)
            logger.info(f"RAW Cache HIT {key}")
            return obj
        except json.JSONDecodeError:
            logger.warning(f"RAW Cache INVALID JSON {key}")
            await self.redis.delete(key)
            return None
        except Exception as e:
            logger.error(f"RAW Cache ERROR get({key}): {e}", exc_info=True)
            return None

    async def set_raw(
        self, *parts: str | UUID, value: dict[str, Any], ttl: int | None = None
    ):
        key = self._key(*parts)
        try:
            payload = json.dumps(value)
            await self.redis.set(key, value=payload, ex=ttl or self.default_ttl)
            logger.info(f"RAW Cache SET {key}")
        except Exception as e:
            logger.error(f"RAW Cache ERROR set({key}): {e}", exc_info=True)

    async def delete(self, *parts: str | UUID):
        key = self._key(*parts)
        try:
            await self.redis.delete(key)
            logger.info(f"Cache DELETE {key}")
        except Exception as e:
            logger.error(f"Cache ERROR delete({key}): {e}", exc_info=True)

    async def delete_by_prefix(
        self, *prefix_parts: str | UUID, batch_size: int = 100
    ) -> None:
        pattern = self._key(*prefix_parts) + "*"
        deleted_total = 0

        try:
            batch = []
            async for key in self.redis.scan_iter(match=pattern, count=batch_size):
                batch.append(key)
                if len(batch) >= batch_size:
                    pipe = self.redis.pipeline()
                    for k in batch:
                        pipe.delete(k)
                    await pipe.execute()
                    deleted_total += len(batch)
                    batch.clear()

            if batch:
                pipe = self.redis.pipeline()
                for k in batch:
                    pipe.delete(k)
                await pipe.execute()
                deleted_total += len(batch)

            logger.info(f"Cache PURGE Deleted {deleted_total} keys matching: {pattern}")
        except Exception as e:
            logger.error(f"Cache ERROR delete_by_prefix({pattern}): {e}", exc_info=True)
