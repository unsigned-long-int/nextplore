import logging 
import httpx 

from dataclasses import dataclass
from typing import Dict, Any
from fastapi import HTTPException, status


logger = logging.getLogger(__name__)

@dataclass
class JWKSFetcher:
    jwks_url: str 

    async def get_jwks(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=5.0)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error('Failed to fetch JWKS from Azure', exc_info=True)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='JWKS fetch failed')
        except httpx.HTTPStatusError as e:
            logger.error('Invalid response from JWKS endpoint', exc_info=True)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='Invalid JWKS response')