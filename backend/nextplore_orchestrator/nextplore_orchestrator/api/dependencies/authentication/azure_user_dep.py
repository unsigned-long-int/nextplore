from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer()


async def get_azure_user(
    request: Request, creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = creds.credentials

    try:
        claims = await request.app.state.token_verifier.verify_token(token)
        return claims
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from e
