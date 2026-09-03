import logging
import os
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from .jwks_fetcher import JWKSFetcher

logger = logging.getLogger(__name__)

JWKS_URL = os.getenv("JWKS_URL")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")
AZURE_AUTHORITY = os.getenv("AZURE_AUTHORITY")

bearer_scheme = HTTPBearer()


class TokenVerifier:
    def __init__(self, jwks_fetcher: JWKSFetcher) -> None:
        self.jwks_fetcher = jwks_fetcher

    async def verify_token(self, token: str) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token header",
            )
        expected_kid = header.get("kid")
        if not expected_kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing kid claim",
            )

        jwks = await self.jwks_fetcher.get_jwks(
            jwks_url=JWKS_URL, expected_kid=expected_kid
        )
        key = next(
            (k for k in jwks.get("keys", []) if k.get("kid") == expected_kid), None
        )
        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown key ID"
            )

        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=JWT_AUDIENCE,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "leeway": 60,
                },
            )
        except JWTError as e:
            logger.debug(f"JWT decode failed for kid={expected_kid}: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed",
            )

        tid = claims.get("tid")
        iss = claims.get("iss")
        if not tid or not iss:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing required claims",
            )

        if iss != f"{AZURE_AUTHORITY}/{tid}/v2.0":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid issuer"
            )

        return claims
