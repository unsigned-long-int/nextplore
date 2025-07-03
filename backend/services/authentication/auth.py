import logging 

from typing import Dict, Any
from jose import jwt, JWTError
from services.settings import settings
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer

from .jwks_fetcher import JWKSFetcher

logger = logging.getLogger(__name__)


bearer_scheme = HTTPBearer()

async def verify_token(token: str, jwks_fetcher: JWKSFetcher) -> Dict[str, Any]:
    jwks = await jwks_fetcher.get_jwks()
    unverified_header = jwt.get_unverified_header(token)

    kid = unverified_header.get('kid')
    if not kid:
        logger.warning('JWT header missing kid')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token header')
    
    key = next((k for k in jwks.get('keys', []) if k.get('kid') == kid), None)
    if not key:
        logger.warning(f'No matching JWKS key found for kid: {kid}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token key not recognized')

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            audience=settings.AZURE_CLIENT_ID,
            issuer=None,
            options={
                'verify_aud': True,
                'verify_exp': True,
                'verify_iss': False
            }
        )

        tenant_id = payload.get('tid')
        actual_issuer = payload.get('iss')
        expected_issuer = f'https://login.microsoftonline.com/{tenant_id}/v2.0'

        if actual_issuer != expected_issuer:
            logger.error('Invalid issuer in token', extra={'actual': actual_issuer, 'expected': expected_issuer})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token issuer')
        return payload
    except JWTError:
        logger.warning('JWT validation failed', exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')