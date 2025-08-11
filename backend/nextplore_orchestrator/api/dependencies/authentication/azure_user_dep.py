from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
bearer_scheme = HTTPBearer()

async def get_azure_user(request: Request, creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = creds.credentials

    try:
        claims = await request.app.state.token_verifier.verify_token(token)
        return claims
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token'
        )