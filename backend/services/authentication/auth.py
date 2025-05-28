from typing import Dict, Any
from jose import jwt, JWTError
import httpx
from services.settings import settings
from fastapi import HTTPException, status

from fastapi.security import HTTPBearer


bearer_scheme = HTTPBearer()


async def get_jwks():
    async with httpx.AsyncClient() as client:
        response = await client.get(settings.JWKS_URL, timeout=5.0)
        response.raise_for_status()
        return response.json()


async def verify_token(token: str):
    jwks = await get_jwks()
    
    try:
        for key in jwks["keys"]:
            print(key)
            try:
                payload = jwt.decode(
                    token,
                    key,
                    algorithms=["RS256"],
                    audience=settings.AZURE_CLIENT_ID,
                    issuer=settings.ISSUER
                )
                return payload
            except JWTError:
                continue
    except Exception as e:
        print("Token verification error:", e)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token"
    )