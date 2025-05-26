from fastapi import Depends, HTTPException, status 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth import verify_token

bearer_scheme = HTTPBearer()

def get_active_user(
        creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = creds.credentials

    try:
        claims = verify_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token'
            )
    return claims