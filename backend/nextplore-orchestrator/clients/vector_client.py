from typing import List

from .base_client import BaseServiceClient
from shared.contracts.vector_service import (
    VectorMetaRequest, 
    VectorMetaResponse,
    VectorStatsResponse
)


class VectorClient(BaseServiceClient):
    def __init__(self, base_url: str = f'http://vector_service:8001') -> None:
        super().__init__(base_url)

    async def get_vector_metas(self, payload: VectorMetaRequest) -> List[VectorMetaResponse]:
        response = await self.post('/v1/vector/get-vector-metas', payload)
        response.raise_for_status()
        return [VectorMetaResponse(**item) for item in response.json()]
    
    async def get_vector_stats(self, payload: VectorMetaRequest) -> VectorStatsResponse:
        response = await self.post('/v1/vector/get-vector-stats', payload)
        response.raise_for_status()
        return VectorStatsResponse(**response.json())