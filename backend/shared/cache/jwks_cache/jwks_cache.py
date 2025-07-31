from typing import Dict, Any, Optional

from shared.cache.utils import get_string_cache_key
from shared.cache.client import BaseCache


class JWKSCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='jwks', version='v1')

    async def get_jwks(
        self,
        jwks_url: str
    ) -> Dict[str, Any]:
        cache_key = get_string_cache_key(jwks_url)
        return await self.get_raw(cache_key)
    
    async def set_jwks(
        self, 
        jwks_url: str,
        data: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> None:
        cache_key = get_string_cache_key(jwks_url)
        await self.set_raw(cache_key, value=data, ttl=ttl)
    

jwks_cache_service = JWKSCache()