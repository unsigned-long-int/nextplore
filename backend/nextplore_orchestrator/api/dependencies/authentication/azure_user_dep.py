from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth import verify_token
from .jwks_fetcher import jwks_fetcher_service

bearer_scheme = HTTPBearer()

async def get_azure_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = creds.credentials

    try:
        claims = await verify_token(token, jwks_fetcher_service)
        return claims
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token'
        )