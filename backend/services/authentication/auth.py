import requests 
from typing import Dict, Any
from jose import jwt, JWTError
from services.settings import settings

_jwls = None 

def _get_jwks():
    global _jwks

    if not _jwls:
        response = requests.get(settings.JWKS_URL)
        response.raise_for_status()
        _jwks = response.json()
    return _jwks


def verify_token(token: str) -> Dict[str, Any]:
    jwks = _get_jwks()

    try:
        print(jwks)
        claims = jwt.decode(
            token,
            jwks,
            algorithms=[settings.JWT_ALGORITHMS],
            audience=settings.AZURE_CLIENT_ID,
            issuer=settings.ISSUER
        )
        return claims 
    except JWTError as e:
        raise ValueError(f'Token validation error: {e}')