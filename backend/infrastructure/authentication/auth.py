import httpx

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt 

from infrastructure.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
JWKS_URL = f'https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/discovery/v2.0/keys'

async def get_jwks():
    async with httpx.AsyncClient() as client:
        res = await client.get(JWKS_URL)
        return res.json()['keys']

async def verify_token(token: str = Depends(oauth2_scheme)):
    keys = await get_jwks()
    for key in keys:
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=settings.AZURE_CLIENT_ID
            )
            return payload
        except:
            continue 
    raise HTTPException(status_code=401, detail='Invalid token')