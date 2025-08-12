import httpx
from typing import List

from clients.base import BaseServiceClient
from nextplore_sdk.contracts.integration_service.prepared_integration_create_request import PreparedIntegrationCreateRequest
from nextplore_sdk.contracts.integration_service.prepared_integration_delete_request import PreparedIntegrationDeleteRequest
from nextplore_sdk.contracts.integration_service.prepared_integration_test_request import PreparedIntegrationTestRequest
from nextplore_sdk.contracts.integration_service.prepared_integration_get_request import PreparedIntegrationGetRequest
from nextplore_sdk.contracts.integration_service.prepared_integration_update_request import PreparedIntegrationUpdateRequest
from nextplore_sdk.contracts.integration_service.integration_profile_response import IntegrationProfileResponse
from nextplore_sdk.contracts.integration_service.filtered_crawl_request import FilteredCrawlRequest
from nextplore_sdk.contracts.integration_service.crawl_response import CrawlResponse
from nextplore_sdk.contracts.integration_service.integration_stats_request import IntegrationStatsRequest
from nextplore_sdk.contracts.integration_service.integration_stats_response import IntegrationStatsResponse
from nextplore_sdk.contracts.integration_service.integration_metadata_request import IntegrationMetadataRequest
from nextplore_sdk.contracts.integration_service.integration_metadata_response import IntegrationMetadataResponse
from .exceptions import IntegrationCrawlRemoteError


class IntegrationClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://integration_service:8001') -> None:
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
        try:
            response = await self.post('/v1/integration/crawl-filtered', payload)
            response.raise_for_status()
            return CrawlResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Crawling failed')
                    failed_ids = detail.get('failed_integration_ids', [])
                    raise IntegrationCrawlRemoteError(message=message, failed_ids=failed_ids)
                except Exception:
                    raise IntegrationCrawlRemoteError('Crawling failed and error response could not be parsed')
            raise

    async def get_integration_stats(self, payload: IntegrationStatsRequest) -> IntegrationStatsResponse:
        response = await self.post('/v1/integration/get-integration-stats', payload)
        response.raise_for_status()
        return IntegrationStatsResponse(**response.json())
