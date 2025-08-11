import logging 
import os
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from fastapi import HTTPException
from fastapi.security import HTTPBearer

from .jwks_fetcher import JWKSFetcher

logger = logging.getLogger(__name__)

JWKS_URL = os.getenv('JWKS_URL')
JWT_AUDIENCE = os.getenv('JWT_AUDIENCE')
AZURE_AUTHORITY = os.getenv('AZURE_AUTHORITY')

bearer_scheme = HTTPBearer()

class TokenVerifier:
    def __init__(self, jwks_fetcher: JWKSFetcher) -> None:
        self.jwks_fetcher = jwks_fetcher

    async def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except JWTError:
            raise HTTPException(401, detail='Invalid token header')

        kid: Optional[str] = header.get('kid')
        if header.get('alg') != 'RS256':
            raise HTTPException(401, detail='Unexpected JWT alg')

        jwks = await self.jwks_fetcher.get_jwks(jwks_url=JWKS_URL, expected_kid=kid)
        keys = jwks.get('keys', [])
        if not keys:
            raise HTTPException(500, detail='No JWKS keys available')

        candidate_keys = [k for k in keys if k.get('kid') == kid] or keys

        last_err: Optional[Exception] = None
        claims: Optional[Dict[str, Any]] = None
        for key in candidate_keys:
            try:
                claims = jwt.decode(
                    token,
                    key,
                    algorithms=['RS256'],
                    audience=JWT_AUDIENCE,
                    options={
                        'verify_signature': True,
                        'verify_aud': True,
                        'verify_exp': True,
                        'verify_iat': True,
                        'leeway': 60,
                    },
                )
                break
            except JWTError as e:
                last_err = e

        if claims is None:
            logger.debug(f'JWT verify failed for kid={kid}, {last_err}', exc_info=True)
            raise HTTPException(401, detail='Token verification failed')

        tid = claims.get('tid')
        iss = claims.get('iss')
        if not tid or not iss:
            raise HTTPException(401, detail='Missing required claims')

        expected_iss_v2 = f'{AZURE_AUTHORITY}/{tid}/v2.0'
        if iss != expected_iss_v2:
            raise HTTPException(401, detail='Invalid issuer')

        return claims