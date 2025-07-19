import os
from fastapi import Depends, HTTPException, status 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from internal_services.authentication import (
    verify_token,
    JWKSFetcher
)


bearer_scheme = HTTPBearer()


async def get_active_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = creds.credentials
    jwk_fetcher = JWKSFetcher(os.getenv('JWKS_URL'))

    try:
        claims = await verify_token(token, jwk_fetcher)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token'
        )
    return claims