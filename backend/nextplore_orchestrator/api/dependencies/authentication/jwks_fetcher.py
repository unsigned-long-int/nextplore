import logging 
import httpx 
import asyncio
import time
import json
import random
import re
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from nextplore_shared.cache.jwks_cache.cache import jwks_cache_service
from .cache_entry import CacheEntry


logger = logging.getLogger(__name__)


_MIN_TTL = 60
_JITTER = 0.10


def _parse_ttl(resp: httpx.Response, default_ttl: int) -> int:
    cc = resp.headers.get('Cache-Control', '')
    m = re.search(r'max-age=(\d+)', cc)
    ttl = int(m.group(1)) if m else default_ttl
    return max(ttl, _MIN_TTL)


def _with_jitter(ttl: int) -> int:
    return max(int(ttl * (1.0 + random.uniform(-_JITTER, _JITTER))), _MIN_TTL)


def _coerce_jwks(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, str):
        obj = json.loads(obj)
    if not isinstance(obj, dict):
        raise ValueError('JWKS is not a JSON object')
    keys = obj.get('keys')
    if not isinstance(keys, list) or not keys:
        raise ValueError('JWKS missing non-empty keys')
    return obj



class JWKSFetcher:
    def __init__(self, ttl: int = 600):
        self.default_ttl = ttl
        self._mem: Dict[str, CacheEntry] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._client = httpx.AsyncClient(timeout=5.0, limits=httpx.Limits(max_connections=10))

    async def get_jwks(self, jwks_url: str, expected_kid: Optional[str] = None) -> Dict[str, Any]:
        now = time.time()
        entry = self._mem.get(jwks_url)

        if entry is not None and now < entry.expires_at and (not expected_kid or expected_kid in entry.kid_index):
            logger.debug(f'JWKS in-memory hit: {jwks_url}')
            return entry.jwks

        try:
            cached = await jwks_cache_service.get_jwks(jwks_url)
            if cached:
                jwks = _coerce_jwks(cached)
                kid_index = {k.get('kid'): k for k in jwks['keys'] if k.get('kid')}
                self._mem[jwks_url] = CacheEntry(
                    jwks=jwks,
                    kid_index=kid_index,
                    expires_at=now + self.default_ttl,
                )
                if not expected_kid or expected_kid in kid_index:
                    logger.debug(f'JWKS dist-cache hit: {jwks_url}')
                    return jwks
        except Exception:
            logger.error(f'JWKS dist-cache read failed for {jwks_url}', exc_info=True)

        lock = self._locks.setdefault(jwks_url, asyncio.Lock())
        async with lock:
            now = time.time()
            entry = self._mem.get(jwks_url)
            if entry is not None and now < entry.expires_at and (not expected_kid or expected_kid in entry.kid_index):
                return entry.jwks

            headers = {}
            if entry and entry.etag:
                headers['If-None-Match'] = entry.etag

            try:
                async with self._client as client:
                    resp = await client.get(jwks_url, headers=headers)
                    if resp.status_code == 304 and entry:
                        ttl = _with_jitter(_parse_ttl(resp, self.default_ttl))
                        entry.expires_at = time.time() + ttl
                        logger.debug(f'JWKS 304 Not Modified: {jwks_url} (extend {ttl})')
                        return entry.jwks

                resp.raise_for_status()
                jwks = _coerce_jwks(resp.json())
                kid_index = {k.get('kid'): k for k in jwks['keys'] if k.get('kid')}
                ttl = _with_jitter(_parse_ttl(resp, self.default_ttl))
                etag = resp.headers.get('ETag')

                new_entry = CacheEntry(
                    jwks=jwks,
                    kid_index=kid_index,
                    expires_at=time.time() + ttl,
                    etag=etag,
                )
                self._mem[jwks_url] = new_entry
                await jwks_cache_service.set_jwks(jwks_url, data=jwks, ttl=ttl)
                return jwks
            except Exception:
                logger.error(f'JWKS fetch failed: {jwks_url}', exc_info=True)
                entry = self._mem.get(jwks_url)
                if entry and (not expected_kid or expected_kid in entry.kid_index):
                    logger.warning(f'Serving STALE JWKS for {jwks_url} due to fetch error')
                    return entry.jwks
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='JWKS fetch failed',
                )

    async def aclose(self) -> None:
        await self._client.aclose()