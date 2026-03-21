import unittest
from uuid import uuid4
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from svc_integration_contracts.models import (
    FilteredCrawlRequest,
    CrawlResponse,
)
from integration_service.services.crawl.exceptions import CrawlIntegrationsFailed
from integration_service.cache import get_cache_service
from integration_service.api.router.crawl_router import router
from integration_service.api.dependencies import get_backend_connector, get_engine_manager, get_repo



class TestCrawlRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.cache_mock = AsyncMock()
        self.repo_mock = AsyncMock()
        self.database_backend_connector_mock = AsyncMock()
        self.engine_manager_mock = AsyncMock()
        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_repo: lambda: self.repo_mock,
            get_backend_connector: lambda: self.database_backend_connector_mock,
            get_engine_manager: lambda: self.engine_manager_mock,
        }

        self.request = FilteredCrawlRequest(
            integrations=[uuid4(), uuid4()],
            schemas={str(uuid4()): ['schema1', 'schema2']},
            tables={str(uuid4()): ['table1', 'table2']},
        )

        self.response = CrawlResponse(
            integration_registry_repr='test-integration',
            integrations_enum=['integration1', 'integration2'],
            schemas_enum=['schemas_1', 'schemas_2'],
            tables_enum=['table1', 'table2'],
            columns_enum=['column1', 'column2'],
            filter_op_enum=['filter1', 'filter2'],
            agg_funcs_enum=['agg_func1', 'agg_func2'],
        )

    def _url(self, org_id, user_id) -> str:
        return (
            f'/v1/integration/organizations/{org_id}/'
            f'users/{user_id}/crawl'
        )

    @patch('integration_service.api.router.crawl_router.get_current_identity')
    def test_returns_cached_integration(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        cached = self.response

        self.cache_mock.get_filtered_integration.return_value = cached
        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(200, response.status_code)
        self.cache_mock.get_filtered_integration.assert_awaited_once()
        self.assertEqual(response.json(), cached.model_dump())

    @patch('integration_service.api.router.crawl_router.crawl_filtered_integration_metadata', new_callable=AsyncMock)
    @patch('integration_service.api.router.crawl_router.get_current_identity')
    def test_filters_integration_and_sets_cache(
        self,
        get_current_identity_mock,
        crawl_filtered_integration_metadata_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock
        self.cache_mock.get_filtered_integration.return_value = None

        crawl_filtered_integration_metadata_mock.return_value = self.response
        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )

        crawl_filtered_integration_metadata_mock.assert_awaited_once()
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), self.response.model_dump())
        self.cache_mock.set_filtered_integration.assert_awaited_once()


    @patch('integration_service.api.router.crawl_router.crawl_filtered_integration_metadata', new_callable=AsyncMock)
    @patch('integration_service.api.router.crawl_router.get_current_identity')
    def test_raises_exception_when_integration_crawl_failed(
        self,
        get_current_identity_mock,
        crawl_filtered_integration_metadata_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock
        self.cache_mock.get_filtered_integration.return_value = None

        crawl_filtered_integration_metadata_mock.side_effect = CrawlIntegrationsFailed('boom!')
        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )
        self.assertEqual(424, response.status_code)
        self.assertIn('boom', response.json()['detail']['message'])
        self.cache_mock.set_filtered_integration.assert_not_awaited()

    @patch('integration_service.api.router.crawl_router.crawl_filtered_integration_metadata', new_callable=AsyncMock)
    @patch('integration_service.api.router.crawl_router.get_current_identity')
    def test_raises_exception_when_generic_error(
        self,
        get_current_identity_mock,
        crawl_filtered_integration_metadata_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock
        self.cache_mock.get_filtered_integration.return_value = None

        crawl_filtered_integration_metadata_mock.side_effect = RuntimeError('boom!')
        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )
        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected error: boom', response.json()['detail']['message'])
        self.cache_mock.set_filtered_integration.assert_not_awaited()
