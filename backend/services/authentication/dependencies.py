from fastapi import Depends, HTTPException, status 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth import verify_token

bearer_scheme = HTTPBearer()

async def get_active_user(
        creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = creds.credentials
    print(token)

    try:
        print('verifying')
        claims = await verify_token(token)
        print('successfully verified')
    except ValueError as e:
        print(str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token'
            )
    return claims