from typing import List

from clients.base import BaseServiceClient
from shared.contracts.vector_service import (
    VectorMetaRequest, 
    VectorMetaResponse,
    VectorStatsRequest,
    VectorStatsResponse,
    QDrantVectorRequest,
    QDrantVectorResponse,
    VectorProfileRequest,
    VectorProfileResponse
)


class VectorClient(BaseServiceClient):
    def __init__(self, base_url: str = f'http://vector_service:8001') -> None:
        super().__init__(base_url)

    async def get_vector_metas(self, payload: VectorMetaRequest) -> List[VectorMetaResponse]:
        response = await self.post('/v1/vector/get-vector-metas', payload)
        response.raise_for_status()
        return [VectorMetaResponse(**item) for item in response.json()]
    
    async def get_vector_stats(self, payload: VectorStatsRequest) -> VectorStatsResponse:
        response = await self.post('/v1/vector/get-vector-stats', payload)
        response.raise_for_status()
        return VectorStatsResponse(**response.json())
    
    async def get_nearest_qdrant_vectors(self, payload: QDrantVectorRequest) -> QDrantVectorResponse:
        response = await self.post('/v1/vector/get-nearest-qdrant-vectors', payload)
        response.raise_for_status()
        return QDrantVectorResponse(**response.json())
    
    async def get_vector_profiles(self, payload: VectorProfileRequest) -> List[VectorProfileResponse]:
        response = await self.post('/v1/vector/get-vector-profiles', payload)
        response.raise_for_status()
        return [VectorProfileResponse(**item) for item in response.json()]
    