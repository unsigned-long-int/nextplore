import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status

from services.integration_registry_crawl_service import CrawlIntegrationsFailed
from api.router.crawl_filtered_integration_router import craw_filtered_integration

import api.router.crawl_filtered_integration_router as router_mod


class TestCrawFilteredIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = SimpleNamespace(user_id='user-123', organization_id='org-456')
        self.payload = object()

    @patch('api.router.crawl_filtered_integration_router.craw_filtered_integration_metadata', new_callable=AsyncMock)
    @patch('api.router.crawl_filtered_integration_router.integration_service_cache')
    @patch('api.router.crawl_filtered_integration_router.get_current_identity')
    async def test_returns_cached_response(self, mock_get_current_identity, mock_cache, mock_crawl):
        mock_get_current_identity.return_value = self.identity

        cached_response = {'ok': True, 'source': 'cache'}
        mock_cache.get_filtered_integration = AsyncMock(return_value=cached_response)
        mock_cache.set_filtered_integration = AsyncMock()

        result = await craw_filtered_integration(self.payload)

        self.assertEqual(result, cached_response)
        mock_cache.get_filtered_integration.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        mock_crawl.assert_not_awaited()
        mock_cache.set_filtered_integration.assert_not_awaited()

    @patch('api.router.crawl_filtered_integration_router.craw_filtered_integration_metadata', new_callable=AsyncMock)
    @patch('api.router.crawl_filtered_integration_router.integration_service_cache')
    @patch('api.router.crawl_filtered_integration_router.get_current_identity')
    async def test_cache_miss_calls_service_and_sets_cache(self, mock_get_current_identity, mock_cache, mock_crawl):
        mock_get_current_identity.return_value = self.identity

        mock_cache.get_filtered_integration = AsyncMock(return_value=None)
        mock_cache.set_filtered_integration = AsyncMock()

        service_response = {'ok': True, 'source': 'service'}
        mock_crawl.return_value = service_response

        result = await craw_filtered_integration(self.payload)

        self.assertEqual(result, service_response)
        mock_cache.get_filtered_integration.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        mock_crawl.assert_awaited_once_with(
            user_id=self.identity.user_id,
            organization_id=self.identity.organization_id,
            inspection_request=self.payload,
        )
        mock_cache.set_filtered_integration.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload, response=service_response
        )

    @patch('api.router.crawl_filtered_integration_router.craw_filtered_integration_metadata', new_callable=AsyncMock)
    @patch('api.router.crawl_filtered_integration_router.integration_service_cache')
    @patch('api.router.crawl_filtered_integration_router.get_current_identity')
    async def test_handles_crawl_integrations_failed(self, mock_get_current_identity, mock_cache, mock_crawl):
        mock_get_current_identity.return_value = self.identity

        mock_cache.get_filtered_integration = AsyncMock(return_value=None)
        mock_cache.set_filtered_integration = AsyncMock()

        class DummyErr(CrawlIntegrationsFailed):
            def __init__(self):
                self.message = 'some integrations failed'
                self.failed_ids = [1, 2, 3]


        err = DummyErr()
        err.message = 'some integrations failed'
        err.failed_ids = [1, 2, 3]

        mock_crawl.side_effect = err

        with self.assertRaises(HTTPException) as ctx:
            await craw_filtered_integration(self.payload)

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertEqual(
            exc.detail,
            {'message': 'some integrations failed', 'failed_integration_ids': ['1', '2', '3']},
        )
        mock_cache.set_filtered_integration.assert_not_awaited()
