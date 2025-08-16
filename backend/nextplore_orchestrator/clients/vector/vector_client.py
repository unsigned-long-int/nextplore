import httpx
from typing import List

from clients.base import BaseServiceClient
from clients.vector.exceptions import (
    VectorSearchDBRemoteError,
    VectorGetMetasRemoteError,
    VectorGetProfilesRemoteError,
    VectorGetStatsRemoteError
)
from nextplore_sdk.contracts.vector_service.vector_meta_request import VectorMetaRequest
from nextplore_sdk.contracts.vector_service.vector_meta_response import VectorMetaResponse
from nextplore_sdk.contracts.vector_service.vector_stats_request import VectorStatsRequest 
from nextplore_sdk.contracts.vector_service.vector_stats_response import VectorStatsResponse
from nextplore_sdk.contracts.vector_service.qdrant_vector_request import QDrantVectorRequest
from nextplore_sdk.contracts.vector_service.qdrant_vector_response import QDrantVectorResponse
from nextplore_sdk.contracts.vector_service.vector_profile_request import VectorProfileRequest
from nextplore_sdk.contracts.vector_service.vector_profile_response import VectorProfileResponse


class VectorClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://vector_service:8001') -> None:
        super().__init__(base_url)

    async def get_vector_metas(self, payload: VectorMetaRequest) -> List[VectorMetaResponse]:
        try:
            response = await self.post('/v1/vector/get-vector-metas', payload)
            response.raise_for_status()
            return [VectorMetaResponse(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get vector metas failed')
                    raise VectorGetMetasRemoteError(message)
                except Exception:
                    raise VectorGetMetasRemoteError('Get vector metas failed and error response could not be parsed')
            raise
    
    async def get_vector_stats(self, payload: VectorStatsRequest) -> VectorStatsResponse:
        try:
            response = await self.post('/v1/vector/get-vector-stats', payload)
            response.raise_for_status()
            return VectorStatsResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get vector stats failed')
                    raise VectorGetStatsRemoteError(message)
                except Exception:
                    raise VectorGetStatsRemoteError('Get vector stats failed and error response could not be parsed')
            raise
    
    async def get_nearest_qdrant_vectors(self, payload: QDrantVectorRequest) -> QDrantVectorResponse:
        try:
            response = await self.post('/v1/vector/get-nearest-qdrant-vectors', payload)
            response.raise_for_status()
            return QDrantVectorResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Search nearest vectors failed')
                    raise VectorSearchDBRemoteError(message)
                except Exception:
                    raise VectorSearchDBRemoteError('Search nearest vectors failed and error response could not be parsed')
            raise

    
    async def get_vector_profiles(self, payload: VectorProfileRequest) -> List[VectorProfileResponse]:
        try:
            response = await self.post('/v1/vector/get-vector-profiles', payload)
            response.raise_for_status()
            return [VectorProfileResponse(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get vector profiles failed')
                    raise VectorGetProfilesRemoteError(message)
                except Exception:
                    raise VectorGetProfilesRemoteError('Get vector profiles failed and error response could not be parsed')
            raise