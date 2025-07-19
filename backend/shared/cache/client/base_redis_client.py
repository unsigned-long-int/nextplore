import logging
from typing import Type, TypeVar, Optional
from redis.asyncio import Redis
from pydantic import BaseModel, ValidationError

from .redis_client_factory import get_redis_client

T = TypeVar('T', bound=BaseModel)
logger = logging.getLogger('shared.cache')

class BaseCache:
    def __init__(
        self,
        namespace: str,
        default_ttl: int = 600,
        redis: Optional[Redis] = None,
        version: Optional[str] = None,
    ):
        self.redis = redis or get_redis_client()
        self.prefix = f'{namespace}:{version + ':' if version else ''}'
        self.default_ttl = default_ttl

    def _key(self, *parts: str) -> str:
        return self.prefix + ':'.join(parts)

    async def get(self, *parts: str, model: Type[T]) -> Optional[T]:
        key = self._key(*parts)
        try:
            cached = await self.redis.get(key)
            if not cached:
                logger.debug(f'[Cache MISS] {key}')
                return None

            obj = model.model_validate_json(cached)
            logger.debug(f'[Cache HIT] {key}')
            return obj
        except ValidationError as ve:
            logger.warning(f'[Cache INVALID DATA] {key}: {ve}')
            await self.redis.delete(key)
            return None
        except Exception as e:
            logger.error(f'[Cache ERROR] get({key}): {e}', exc_info=True)
            return None

    async def set(self, *parts: str, value: BaseModel, ttl: Optional[int] = None):
        key = self._key(*parts)
        try:
            payload = value.model_dump_json()
            await self.redis.set(key, value=payload, ex=ttl or self.default_ttl)
            logger.debug(f'[Cache SET] {key}')
        except Exception as e:
            logger.error(f'[Cache ERROR] set({key}): {e}', exc_info=True)

    async def delete(self, *parts: str):
        key = self._key(*parts)
        try:
            await self.redis.delete(key)
            logger.debug(f'[Cache DELETE] {key}')
        except Exception as e:
            logger.error(f'[Cache ERROR] delete({key}): {e}', exc_info=True)

