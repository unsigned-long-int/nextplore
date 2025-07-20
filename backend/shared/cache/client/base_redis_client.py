import logging
import json
from typing import Type, TypeVar, Optional, List
from uuid import UUID
from redis.asyncio import Redis
from pydantic import BaseModel, ValidationError, TypeAdapter
from pydantic.json import pydantic_encoder

from .redis_client_factory import get_redis_client


T = TypeVar('T', bound=BaseModel)
logger = logging.getLogger(__name__)

class BaseCache:
    def __init__(
        self,
        namespace: str,
        default_ttl: int = 600,
        redis: Optional[Redis] = None,
        version: Optional[str] = None,
    ):
        self.redis = redis or get_redis_client()
        self.prefix =f'{namespace}:{version}:' if version else f'{namespace}:'
        self.default_ttl = default_ttl

    def _key(self, *parts: str | UUID) -> str:
        return self.prefix + ':'.join(str(part) for part in parts)

    async def get_one(self, *parts: str | UUID, model: Type[T]) -> Optional[T]:
        key = self._key(*parts)
        try:
            cached = await self.redis.get(key)
            if not cached:
                logger.debug(f'[Cache MISS] {key}')
                return None
            
            obj = model.model_validate_json(cached)
            logger.debug(f'[Cache HIT] {key}')
            return obj
        except (ValidationError, json.JSONDecodeError) as e:
            logger.warning(f'[Cache INVALID DATA] {key}: {e}')
            await self.redis.delete(key)
            return None
        except Exception as e:
            logger.error(f'[Cache ERROR] get({key}): {e}', exc_info=True)
            return None
        
    async def set_one(self, *parts: str | UUID, value: BaseModel, ttl: Optional[int] = None):
        key = self._key(*parts)
        try:
            payload = value.model_dump_json()
            await self.redis.set(key, value=payload, ex=ttl or self.default_ttl)
            logger.debug(f'[Cache SET] {key}')
        except Exception as e:
            logger.error(f'[Cache ERROR] set({key}): {e}', exc_info=True)

    async def get_many(self, *parts: str | UUID, model: Type[T]) -> Optional[List[T]]:
        key = self._key(*parts)
        try:
            cached = await self.redis.get(key)
            if not cached:
                logger.debug(f'[Cache MISS]: {key}')
                return None

            parsed = json.loads(cached)
            result = TypeAdapter(List[model]).validate_python(parsed)
            logger.debug(f'[Cache HIT] {key}')
            return result
        except (ValidationError, json.JSONDecodeError) as ve:
            logger.warning(f'[Cache INVALID LIST DATA] {key}: {ve}')
            await self.redis.delete(key)
            return []
        except Exception as e:
            logger.error(f'[Cache ERROR] get_many({key}): {e}', exc_info=True)
            return []
    
    async def set_many(self, *parts: str | UUID, value: List[BaseModel], ttl: Optional[int] = None):
        key = self._key(*parts)
        try:
            payload = json.dumps(value, default=pydantic_encoder)
            await self.redis.set(key, value=payload, ex=ttl or self.default_ttl)
            logger.debug(f'[Cache SET LIST] {key}')
        except Exception as e:
            logger.error(f'[Cache ERROR] set_many({key}): {e}', exc_info=True)

    async def delete(self, *parts: str | UUID):
        key = self._key(*parts)
        try:
            await self.redis.delete(key)
            logger.debug(f'[Cache DELETE] {key}')
        except Exception as e:
            logger.error(f'[Cache ERROR] delete({key}): {e}', exc_info=True)

