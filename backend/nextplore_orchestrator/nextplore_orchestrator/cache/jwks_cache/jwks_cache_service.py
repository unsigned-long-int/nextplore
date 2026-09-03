from typing import Any

from nextplore_sdk.cache.client.interface import Cache
from nextplore_sdk.cache.utils.key_factory import get_string_cache_key


class JWKSCacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    async def get_jwks(self, jwks_url: str) -> dict[str, Any]:
        cache_key = get_string_cache_key(jwks_url)
        return await self.cache.get_raw(cache_key)

    async def set_jwks(
        self, jwks_url: str, data: dict[str, Any], ttl: int | None = None
    ) -> None:
        cache_key = get_string_cache_key(jwks_url)
        await self.cache.set_raw(cache_key, value=data, ttl=ttl)
