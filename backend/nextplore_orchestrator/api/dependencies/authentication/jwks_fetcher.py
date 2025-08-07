import logging 
import httpx 
import asyncio
import time
import json
from typing import Dict, Any, Tuple
from fastapi import HTTPException, status

from nextplore_shared.cache.jwks_cache.cache import jwks_cache_service


logger = logging.getLogger(__name__)


class JWKSFetcher:
    def __init__(self, ttl: int = 600):
        self.ttl = ttl

        self._in_memory_cache: Dict[str, Tuple[Dict, float]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def get_jwks(self, jwks_url: str) -> Dict[str, Any]:
        now = time.time()

        if jwks_url in self._in_memory_cache:
            jwks, expires_at = self._in_memory_cache[jwks_url]
            if now < expires_at:
                logger.info(f'JWKS IN-MEMORY HIT for {jwks_url}')
                return jwks
            
        jwks = await jwks_cache_service.get_jwks(jwks_url)
        if jwks:
            try:
                self._in_memory_cache[jwks_url] = (jwks, now + self.ttl)
                return jwks
            except json.JSONDecodeError:
                await jwks_cache_service.set_jwks(jwks_url, ttl=self.ttl)

        lock = self._locks.setdefault(jwks_url, asyncio.Lock())
        async with lock:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(jwks_url, timeout=5.0)
                    resp.raise_for_status()
                    jwks = resp.json()
            except Exception:
                logger.error(f'JWKS fetch failed from {jwks_url}', exc_info=True)
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='JWKS fetch failed')

            self._in_memory_cache[jwks_url] = (jwks, time.time() + self.ttl)
            await jwks_cache_service.set_jwks(jwks_url, data=jwks, ttl=self.ttl)

            return jwks

    
jwks_fetcher_service = JWKSFetcher(ttl=600)