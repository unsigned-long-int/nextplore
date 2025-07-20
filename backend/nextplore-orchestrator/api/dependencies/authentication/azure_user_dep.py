import os
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth import verify_token
from .jwks_fetcher import JWKSFetcher

bearer_scheme = HTTPBearer()

async def get_azure_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = creds.credentials
    jwk_fetcher = JWKSFetcher(os.getenv('JWKS_URL'))

    try:
        claims = await verify_token(token, jwk_fetcher)
        return claims
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token'
        )