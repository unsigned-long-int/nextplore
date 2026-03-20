import httpx
from uuid import UUID
from typing import List
from json import JSONDecodeError

from nextplore_orchestrator.clients.base import BaseServiceClient
from nextplore_orchestrator.clients.vector.exceptions import (
    VectorSearchDBRemoteError,
    VectorGetMetasRemoteError,
    VectorGetProfilesRemoteError,
    VectorGetStatsRemoteError
)

from svc_vector_contracts.models import (
    EmbeddingQuery,
    VectorSearchResult,
    VectorMetadataQuery,
    TableProfile,
    VectorIndexStats,
    TableMetadata,
    VectorMetadata
)



class VectorClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://vector_service:8001') -> None:
        super().__init__(base_url)

    async def get_meta(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: VectorMetadataQuery
    ) -> List[VectorMetadata]:
        try:
            url = f'/v1/vector/organizations/{organization_id}/users/{user_id}/integrations/vectors/meta'
            response = await self.post(url, payload.model_dump())
            response.raise_for_status()
            return [VectorMetadata(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get vector metas failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Get vector metas failed and error response could not be parsed'
                raise VectorGetMetasRemoteError(message)
            raise
    
    async def get_stats(self, organization_id: UUID, user_id: UUID) -> VectorIndexStats:
        try:
            url = f'/v1/vector/organizations/{organization_id}/users/{user_id}/stats'
            response = await self.get(url)
            response.raise_for_status()
            return VectorIndexStats(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get vector stats failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Get vector stats failed and error response could not be parsed'
                raise VectorGetStatsRemoteError(message)
            raise
    
    async def get_nearest_neighbours(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: EmbeddingQuery
    ) -> List[VectorSearchResult]:
        try:
            url = f'/v1/vector/organizations/{organization_id}/users/{user_id}/nearest-neighbours'
            response = await self.post(url, payload.model_dump())
            response.raise_for_status()
            return [VectorSearchResult(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Search nearest vectors failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Search nearest vectors failed and error response could not be parsed'
                raise VectorSearchDBRemoteError(message)
            raise

    async def get_profiles(
        self,
        organization_id: UUID,
        user_id: UUID,
        integration_id: UUID
    ) -> List[TableProfile]:
        try:
            url = f'/v1/vector/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}/vectors/profiles'
            response = await self.get(url)
            response.raise_for_status()
            return [TableProfile(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get vector profiles failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Get vector profiles failed and error response could not be parsed'
                raise VectorGetProfilesRemoteError(message)
            raise
