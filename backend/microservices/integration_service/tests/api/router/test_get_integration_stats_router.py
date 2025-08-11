import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from api.router.get_integration_stats_router import get_integration_stats


class TestGetIntegrationStats(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = SimpleNamespace(user_id=uuid4(), organization_id=uuid4())
        self.payload = SimpleNamespace(
            user_id=uuid4(),
            organization_id=uuid4(),
        )
        self.connector = object()

    @patch('api.router.get_integration_stats_router.IntegrationStatsResponse')
    @patch('api.router.get_integration_stats_router.IntegrationRepository')
    @patch('api.router.get_integration_stats_router.integration_service_cache')
    @patch('api.router.get_integration_stats_router.get_current_identity')
    async def test_returns_cached_response(self, mock_get_current_identity, mock_cache, repo_cls, resp_cls):
        mock_get_current_identity.return_value = self.identity

        cached = {'from': 'cache'}
        mock_cache.get_integration_stats = AsyncMock(return_value=cached)
        mock_cache.set_integration_stats = AsyncMock()

        result = await get_integration_stats(self.payload, connector=self.connector)

        self.assertIs(result, cached)
        mock_cache.get_integration_stats.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        repo_cls.assert_not_called()
        resp_cls.assert_not_called()
        mock_cache.set_integration_stats.assert_not_awaited()

    @patch('api.router.get_integration_stats_router.integration_service_cache')
    @patch('api.router.get_integration_stats_router.IntegrationStatsResponse')
    @patch('api.router.get_integration_stats_router.IntegrationRepository')
    @patch('api.router.get_integration_stats_router.get_current_identity')
    async def test_cache_miss_builds_response_and_sets_cache(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_resp_cls,
        mock_cache,
    ):
        mock_get_current_identity.return_value = self.identity
        mock_cache.get_integration_stats = AsyncMock(return_value=None)
        mock_cache.set_integration_stats = AsyncMock()

        repo = Mock()
        integration_ids = [uuid4(), uuid4(), uuid4()]
        repo.get_user_integration_ids = AsyncMock(return_value=integration_ids)
        mock_repo_cls.return_value = repo

        mock_resp_cls.side_effect = lambda **kwargs: kwargs 

        result = await get_integration_stats(self.payload, connector=self.connector)

        self.assertEqual(result['integration_ids'], integration_ids)
        self.assertEqual(result['integration_count'], len(integration_ids))

        mock_cache.get_integration_stats.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        repo.get_user_integration_ids.assert_awaited_once_with(
            user_id=self.payload.user_id,
            organization_id=self.payload.organization_id,
        )
        mock_resp_cls.assert_called_once_with(
            integration_ids=integration_ids,
            integration_count=len(integration_ids),
        )
        mock_cache.set_integration_stats.assert_awaited_once_with(
            user_identity=self.identity,
            request=self.payload,
            response=result,
        )

    @patch('api.router.get_integration_stats_router.integration_service_cache')
    @patch('api.router.get_integration_stats_router.IntegrationRepository')
    @patch('api.router.get_integration_stats_router.get_current_identity')
    async def test_integration_get_failed_raises_424(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_cache,
    ):
        mock_get_current_identity.return_value = self.identity
        mock_cache.get_integration_stats = AsyncMock(return_value=None)
        mock_cache.set_
