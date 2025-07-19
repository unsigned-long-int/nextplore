import httpx 
from pydantic import BaseModel 
from fastapi.encoders import jsonable_encoder


class BaseServiceClient:
    def __init__(self, base_url: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(20.0, connect=3.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)    
        )

    async def post(self, path: str, payload: BaseModel):
        response = await self.client.post(path, json=jsonable_encoder(payload))
        response.raise_for_status()
        return response 
    
    async def close(self) -> None:
        await self.client.aclose()