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
from nextplore_orchestrator.clients.vector.models.vector_meta_request import VectorMetaRequest
from nextplore_orchestrator.clients.vector.models.vector_meta_response import VectorMetaResponse
from nextplore_orchestrator.clients.vector.models.vector_stats_response import VectorStatsResponse
from nextplore_orchestrator.clients.vector.models.qdrant_vector_request import QDrantVectorRequest
from nextplore_orchestrator.clients.vector.models.qdrant_vector_response import QDrantVectorResponse
from nextplore_orchestrator.clients.vector.models.vector_profile_response import VectorProfileResponse


class VectorClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://vector_service:8001') -> None:
        super().__init__(base_url)

    async def get_meta(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: VectorMetaRequest
    ) -> List[VectorMetaResponse]:
        try:
            url = f'/v1/vector/organizations/{organization_id}/users/{user_id}/integrations/vectors/meta'
            response = await self.get(url, payload.model_dump())
            response.raise_for_status()
            return [VectorMetaResponse(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get vector metas failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Get vector metas failed and error response could not be parsed'
                raise VectorGetMetasRemoteError(message)
            raise
    
    async def get_stats(self, organization_id: UUID, user_id: UUID) -> VectorStatsResponse:
        try:
            url = f'/v1/vector/organizations/{organization_id}/users/{user_id}/stats'
            response = await self.get(url)
            response.raise_for_status()
            return VectorStatsResponse(**response.json())
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
        payload: QDrantVectorRequest
    ) -> QDrantVectorResponse:
        try:
            url = f'/v1/vector/organizations/{organization_id}/users/{user_id}/nearest-neighbours'
            response = await self.post(url, payload.model_dump())
            response.raise_for_status()
            return QDrantVectorResponse(**response.json())
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
    ) -> List[VectorProfileResponse]:
        try:
            url = f'/v1/vector/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}/vectors/profiles'
            response = await self.get(url)
            response.raise_for_status()
            return [VectorProfileResponse(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get vector profiles failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Get vector profiles failed and error response could not be parsed'
                raise VectorGetProfilesRemoteError(message)
            raise
