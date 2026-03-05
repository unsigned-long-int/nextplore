import httpx
from typing import List
from uuid import UUID
from json import JSONDecodeError

from nextplore_orchestrator.clients.base import BaseServiceClient
from svc_integration_contracts.models import (
    IntegrationCreateRequest,
    IntegrationUpdateRequest,
    IntegrationProfile,
    FilteredCrawlRequest,
    CrawlResponse,
    IntegrationStatsResponse,
    IntegrationConnectionProfile,
    CertProfile,
    CertCreateRequest
)
from .exceptions import (
    IntegrationCrawlRemoteError,
    IntegrationCreateRemoteError,
    IntegrationDeleteRemoteError,
    IntegrationGetRemoteError,
    IntegrationGetProfilesRemoteError,
    IntegrationGetStatsRemoteError,
    IntegrationTestRemoteError,
    IntegrationUpdateRemoteError,
    CertGetProfilesRemoteError,
    CertCreateRemoteError
)


class IntegrationClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://integration_service:8001') -> None:
        super().__init__(base_url)

    async def get_profiles(self, organization_id: UUID, user_id: UUID) -> List[IntegrationProfile]:
        try:
            url = f'/v1/integration/organizations/{organization_id}/users/{user_id}/integrations/profiles'
            response = await self.get(url)
            response.raise_for_status()
            return [IntegrationProfile(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get integration profiles failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Get integration profiles failed and error response could not be parsed'
                raise IntegrationGetProfilesRemoteError(message)
            raise
    
    async def update_integration(
        self,
        organization_id: UUID,
        user_id: UUID,
        integration_id: UUID,
        payload: IntegrationUpdateRequest
    ) -> None:
        try:
            url = f'/v1/integration/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}'
            response = await self.patch(url, payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Update integration failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Update integration failed and error response could not be parsed'
                raise IntegrationUpdateRemoteError(message)
            raise
    
    async def get_connection_profile(
        self,
        organization_id: UUID,
        user_id: UUID,
        integration_id: UUID
    ) -> IntegrationConnectionProfile:
        try:
            url = f'/v1/integration/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}/connection-profile'
            response = await self.get(url)
            response.raise_for_status()
            return IntegrationConnectionProfile(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get single integration failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Get single integration failed and error response could not be parsed'
                raise IntegrationGetRemoteError(message)
            raise
    
    async def create_integration(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: IntegrationCreateRequest
    ) -> None:
        try:
            url = f'/v1/integration/organizations/{organization_id}/users/{user_id}/integrations'
            response = await self.post(url, payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Create integration failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Create integration failed and error response could not be parsed'
                raise IntegrationCreateRemoteError(message)
            raise

    async def test_integration(
        self,
        payload: IntegrationCreateRequest
    ) -> None:
        try:
            url = '/v1/integration/test'
            response = await self.post(url, payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Test integration failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Test integration failed and error response could not be parsed'
                raise IntegrationTestRemoteError(message)
            raise

    async def delete_integration(
        self,
        organization_id: UUID,
        user_id: UUID,
        integration_id: UUID
    ) -> None:
        try:
            url = f'/v1/integration/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}'
            response = await self.delete(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Delete integration failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Delete integration failed and error response could not be parsed'
                raise IntegrationDeleteRemoteError(message)
            raise

    async def crawl_filtered_integration(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: FilteredCrawlRequest
    ) -> CrawlResponse:
        try:
            url = f'/v1/integration/organizations/{organization_id}/users/{user_id}/crawl'
            response = await self.post(url, payload)
            response.raise_for_status()
            return CrawlResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Crawling failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Crawling failed and error response could not be parsed'
                raise IntegrationCrawlRemoteError(message)
            raise

    async def get_stats(self, organization_id: UUID, user_id: UUID) -> IntegrationStatsResponse:
        try:
            url = f'/v1/integration/organizations/{organization_id}/users/{user_id}/stats'
            response = await self.get(url)
            response.raise_for_status()
            return IntegrationStatsResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get integration stats failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Get integration stats failed and error response could not be parsed'
                raise IntegrationGetStatsRemoteError(message)
            raise

    async def get_cert_profiles(self, organization_id: UUID, user_id: UUID) -> List[CertProfile]:
        try:
            url = f'/v1/integration/organizations/{organization_id}/users/{user_id}/integrations/certificates/profiles'
            response = await self.get(url)
            response.raise_for_status()
            return [CertProfile(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Get certificate profiles failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Get certificates failed and error response could not be parsed'
                raise CertGetProfilesRemoteError(message)
            raise

    async def create_cert(self, organization_id: UUID, user_id: UUID, payload: CertCreateRequest) -> None:
        try:
            url = f'/v1/integration/organizations/{organization_id}/users/{user_id}/integrations/certificates'
            response = await self.post(url, payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Create certificate failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message =  'Create certificate failed and error response could not be parsed'
                raise CertCreateRemoteError(message)
            raise
