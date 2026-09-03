from json import JSONDecodeError
from uuid import UUID

import httpx
from svc_integration_contracts.models import (
    CertCreateRequest,
    CertProfile,
    CrawlResponse,
    DataStoreConnectionProfile,
    DataStoreCreateRequest,
    DataStoreProfile,
    DataStoreStatsResponse,
    DataStoreUpdateRequest,
    FilteredCrawlRequest,
    UserLlmConfig,
    UserLlmCreateRequest,
    UserLlmProfile,
)

from nextplore_orchestrator.clients.base import BaseServiceClient

from .exceptions import (
    CertCreateRemoteError,
    CertGetProfilesRemoteError,
    DataStoreCrawlRemoteError,
    DataStoreCreateRemoteError,
    DataStoreDeleteRemoteError,
    DataStoreGetProfilesRemoteError,
    DataStoreGetRemoteError,
    DataStoreGetStatsRemoteError,
    DataStoreTestRemoteError,
    DataStoreUpdateRemoteError,
    LlmCreateRemoteError,
    LlmGetConfigRemoteError,
    LlmGetProfilesRemoteError,
)


class IntegrationClient(BaseServiceClient):
    def __init__(self, base_url: str = "http://integration_service:8001") -> None:
        super().__init__(base_url)

    async def get_datastore_profiles(
        self, organization_id: UUID, user_id: UUID
    ) -> list[DataStoreProfile]:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/datastores/profiles"
            response = await self.get(url)
            response.raise_for_status()
            return [DataStoreProfile(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Get data store profiles failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = "Get data store profiles failed and error response could not be parsed"
                raise DataStoreGetProfilesRemoteError(message)
            raise

    async def update_datastore(
        self,
        organization_id: UUID,
        user_id: UUID,
        datastore_id: UUID,
        payload: DataStoreUpdateRequest,
    ) -> None:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/datastores/{datastore_id}"
            response = await self.patch(url, payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Update data store failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = "Update data store failed and error response could not be parsed"
                raise DataStoreUpdateRemoteError(message)
            raise

    async def get_datastore_connection_profile(
        self, organization_id: UUID, user_id: UUID, datastore_id: UUID
    ) -> DataStoreConnectionProfile:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/datastores/{datastore_id}/connection-profile"
            response = await self.get(url)
            response.raise_for_status()
            return DataStoreConnectionProfile(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Get single data store failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = "Get single data store failed and error response could not be parsed"
                raise DataStoreGetRemoteError(message)
            raise

    async def create_datastore(
        self, organization_id: UUID, user_id: UUID, payload: DataStoreCreateRequest
    ) -> None:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/datastores"
            response = await self.post(url, payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Create data store failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = "Create data store failed and error response could not be parsed"
                raise DataStoreCreateRemoteError(message)
            raise

    async def create_user_llm(
        self, organization_id: UUID, user_id: UUID, payload: UserLlmCreateRequest
    ) -> None:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/llm"
            response = await self.post(url, payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Create user llm failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = (
                        "Create llm model failed and error response could not be parsed"
                    )
                raise LlmCreateRemoteError(message)
            raise

    async def test_datastore(self, payload: DataStoreCreateRequest) -> None:
        try:
            url = "/v1/integration/datastores/test"
            response = await self.post(url, payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Test data store failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = (
                        "Test data store failed and error response could not be parsed"
                    )
                raise DataStoreTestRemoteError(message)
            raise

    async def delete_datastore(
        self, organization_id: UUID, user_id: UUID, datastore_id: UUID
    ) -> None:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/datastores/{datastore_id}"
            response = await self.delete(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Delete data store failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = "Delete data store failed and error response could not be parsed"
                raise DataStoreDeleteRemoteError(message)
            raise

    async def crawl_filtered_datastore(
        self, organization_id: UUID, user_id: UUID, payload: FilteredCrawlRequest
    ) -> CrawlResponse:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/datastores/crawl"
            response = await self.post(url, payload)
            response.raise_for_status()
            return CrawlResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Crawling failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = "Crawling failed and error response could not be parsed"
                raise DataStoreCrawlRemoteError(message)
            raise

    async def get_stats(
        self, organization_id: UUID, user_id: UUID
    ) -> DataStoreStatsResponse:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/datastores/stats"
            response = await self.get(url)
            response.raise_for_status()
            return DataStoreStatsResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Get data store stats failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = "Get data store stats failed and error response could not be parsed"
                raise DataStoreGetStatsRemoteError(message)
            raise

    async def get_cert_profiles(
        self, organization_id: UUID, user_id: UUID
    ) -> list[CertProfile]:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/datastores/certificates/profiles"
            response = await self.get(url)
            response.raise_for_status()
            return [CertProfile(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Get certificate profiles failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = (
                        "Get certificates failed and error response could not be parsed"
                    )
                raise CertGetProfilesRemoteError(message)
            raise

    async def create_cert(
        self, organization_id: UUID, user_id: UUID, payload: CertCreateRequest
    ) -> None:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/datastores/certificates"
            response = await self.post(url, payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Create certificate failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = "Create certificate failed and error response could not be parsed"
                raise CertCreateRemoteError(message)
            raise

    async def get_user_llm_profiles(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> list[UserLlmProfile]:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/llm/profiles"
            response = await self.get(url)
            response.raise_for_status()
            return [UserLlmProfile(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Get llm profiles failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = (
                        "Get llm profiles failed and error response could not be parsed"
                    )
                raise LlmGetProfilesRemoteError(message)
            raise

    async def get_user_llm_config(
        self, organization_id: UUID, user_id: UUID, model_id: UUID
    ) -> UserLlmConfig:
        try:
            url = f"/v1/integration/organizations/{organization_id}/users/{user_id}/llm/{model_id}/config"
            response = await self.get(url)
            response.raise_for_status()
            return UserLlmConfig(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get("detail", {})
                    message = detail.get("message", "Get llm config failed")
                except (JSONDecodeError, KeyError, TypeError):
                    message = (
                        "Get llm config failed and error response could not be parsed"
                    )
                raise LlmGetConfigRemoteError(message)
            raise
