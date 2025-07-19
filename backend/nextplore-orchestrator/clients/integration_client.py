from typing import List
from uuid import UUID

from .base_client import BaseServiceClient
from shared.contracts.integration_service import (
    PreparedIntegrationCreateRequest,
    PreparedIntegrationDeleteRequest,
    PreparedIntegrationTestRequest,
    PreparedIntegrationGetRequest,
    PreparedIntegrationUpdateRequest,
    IntegrationProfileResponse,
    FilteredCrawlRequest, 
    InitialCrawlRequest,
    CrawlResponse,
    IntegrationStatsRequest,
    IntegrationStatsResponse,
    IntegrationMetadataRequest,
    IntegrationMetadataResponse
)   


class IntegrationClient(BaseServiceClient):
    def __init__(self, base_url: str = f'http://integration_service:8001') -> None:
        super().__init__(base_url)


    async def get_integrations(self, payload: PreparedIntegrationGetRequest) -> List[IntegrationProfileResponse]:
        response = await self.post('/v1/integration/get-integrations', payload)
        response.raise_for_status()
        return [IntegrationProfileResponse(**item) for item in response.json()]
    

    async def update_integration(self, payload: PreparedIntegrationUpdateRequest) -> None:
        response = await self.post('/v1/integration/update-integration', payload)
        response.raise_for_status()
    

    async def get_integration(self, payload: IntegrationMetadataRequest) -> IntegrationMetadataResponse:
        response = await self.post('/v1/integration/get-integration', payload)
        response.raise_for_status()
        return IntegrationMetadataResponse(**response.json())
    

    async def create_integration(self, payload: PreparedIntegrationCreateRequest) -> None:
        response = await self.post('/v1/integration/create-integration', payload)
        response.raise_for_status()

    async def test_integration(self, payload: PreparedIntegrationTestRequest) -> None:
        response = await self.post('/v1/integration/test-integration', payload)
        response.raise_for_status()

    async def delete_integration(self, payload: PreparedIntegrationDeleteRequest) -> None:
        response = await self.post('/v1/integration/delete-integration', payload)
        response.raise_for_status()

    async def crawl_filtered_integration(self, payload: FilteredCrawlRequest) -> CrawlResponse:
        response = await self.post('/v1/integration/crawl-filtered', payload)
        response.raise_for_status()
        return CrawlResponse(**response.json())
    
    async def crawl_initial_integration(self, integration_id: UUID) -> None:
        payload = InitialCrawlRequest(integration_id=integration_id)
        response = await self.post('/v1/integration/crawl-initial', payload)
        response.raise_for_status()

    async def get_integration_stats(self, payload: IntegrationStatsRequest) -> IntegrationStatsResponse:
        response = await self.post('/v1/integration/get-integration-stats', payload)
        response.raise_for_status()
        return IntegrationStatsResponse(**response.json())
