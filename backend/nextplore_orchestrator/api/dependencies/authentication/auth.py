import logging 
import os
from typing import Dict, Any
from jose import jwt, JWTError
from fastapi import HTTPException
from fastapi.security import HTTPBearer

from .jwks_fetcher import JWKSFetcher

logger = logging.getLogger(__name__)


bearer_scheme = HTTPBearer()

async def verify_token(token: str, jwks_fetcher: JWKSFetcher) -> Dict[str, Any]:
    try:
        unverified_header = jwt.get_unverified_header(token)
        unverified_payload = jwt.get_unverified_claims(token)
    except JWTError:
        raise HTTPException(401, detail='Invalid token')

    kid = unverified_header.get('kid')
    tenant_id = unverified_payload.get('tid')
    issuer = unverified_payload.get('iss')

    if not kid or not tenant_id or not issuer:
        raise HTTPException(401, detail='Missing required claims')

    jwks_url = f'https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys'
    jwks = await jwks_fetcher.get_jwks(jwks_url)

    key = next((k for k in jwks['keys'] if k['kid'] == kid), None)
    if not key:
        raise HTTPException(401, detail='Unknown key')

    try:
        return jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            audience=os.getenv('AZURE_CLIENT_ID'),
            issuer=issuer
        )
    except JWTError:
        raise HTTPException(401, detail='Token verification failed')
