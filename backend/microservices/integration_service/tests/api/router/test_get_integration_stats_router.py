import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status

from api.router.get_integration_stats_router import get_integration_stats


class TestGetIntegrationStats(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = SimpleNamespace(user_id=uuid4(), organization_id=uuid4())
        self.payload = SimpleNamespace(
            user_id=uuid4(),
            organization_id=uuid4(),
        )
        self.connector = object()
        self.cache_service = SimpleNamespace(
            get_integration_stats=AsyncMock(),
            set_integration_stats=AsyncMock(),
        )

    @patch('api.router.get_integration_stats_router.IntegrationRepository')
    @patch('api.router.get_integration_stats_router.IntegrationStatsResponse')
    @patch('api.router.get_integration_stats_router.get_current_identity')
    async def test_returns_cached_response(
        self,
        mock_get_current_identity,
        mock_resp_cls,
        mock_repo_cls,
    ):
        mock_get_current_identity.return_value = self.identity

        cached = {'from': 'cache'}
        self.cache_service.get_integration_stats.return_value = cached

        result = await get_integration_stats(
            self.payload,
            connector=self.connector,
            cache_service=self.cache_service
        )

        self.assertIs(result, cached)
        self.cache_service.get_integration_stats.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        mock_repo_cls.assert_not_called()
        mock_resp_cls.assert_not_called()
        self.cache_service.set_integration_stats.assert_not_awaited()

    @patch('api.router.get_integration_stats_router.IntegrationRepository')
    @patch('api.router.get_integration_stats_router.IntegrationStatsResponse')
    @patch('api.router.get_integration_stats_router.get_current_identity')
    async def test_cache_miss_builds_response_and_sets_cache(
        self,
        mock_get_current_identity,
        mock_resp_cls,
        mock_repo_cls,
    ):
        mock_get_current_identity.return_value = self.identity
        self.cache_service.get_integration_stats.return_value = None

        integration_ids = [uuid4(), uuid4(), uuid4()]
        repo = Mock()
        repo.get_user_integration_ids = AsyncMock(return_value=integration_ids)
        mock_repo_cls.return_value = repo

        mock_resp_cls.side_effect = lambda **kwargs: kwargs

        result = await get_integration_stats(
            self.payload,
            connector=self.connector,
            cache_service=self.cache_service
        )

        self.assertEqual(result['integration_ids'], integration_ids)
        self.assertEqual(result['integration_count'], len(integration_ids))

        self.cache_service.get_integration_stats.assert_awaited_once_with(
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
        self.cache_service.set_integration_stats.assert_awaited_once_with(
            user_identity=self.identity,
            request=self.payload,
            response=result,
        )

    @patch('api.router.get_integration_stats_router.IntegrationRepository')
    @patch('api.router.get_integration_stats_router.get_current_identity')
    async def test_integration_get_failed_raises_424_and_no_cache_set(
        self,
        mock_get_current_identity,
        mock_repo_cls,
    ):
        mock_get_current_identity.return_value = self.identity
        self.cache_service.get_integration_stats.return_value = None

        from database.exceptions import IntegrationGetFailed

        class DummyGetFailed(IntegrationGetFailed):
            def __str__(self):
                return 'db fail'

        repo = Mock()
        repo.get_user_integration_ids = AsyncMock(side_effect=DummyGetFailed())
        mock_repo_cls.return_value = repo

        with self.assertRaises(HTTPException) as ctx:
            await get_integration_stats(
                self.payload,
                connector=self.connector,
                cache_service=self.cache_service
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertEqual(exc.detail, {'message': 'Database error: db fail'})
        self.cache_service.set_integration_stats.assert_not_awaited()

    @patch('api.router.get_integration_stats_router.IntegrationRepository')
    @patch('api.router.get_integration_stats_router.get_current_identity')
    async def test_unexpected_error_raises_500_and_no_cache_set(
        self,
        mock_get_current_identity,
        mock_repo_cls,
    ):
        mock_get_current_identity.return_value = self.identity
        self.cache_service.get_integration_stats.return_value = None

        repo = Mock()
        repo.get_user_integration_ids = AsyncMock(side_effect=RuntimeError('boom'))
        mock_repo_cls.return_value = repo

        with self.assertRaises(HTTPException) as ctx:
            await get_integration_stats(
                self.payload,
                connector=self.connector,
                cache_service=self.cache_service
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(exc.detail, {'message': 'Unexpected error: boom'})
        self.cache_service.set_integration_stats.assert_not_awaited()
