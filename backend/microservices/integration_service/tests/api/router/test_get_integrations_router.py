import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status

from api.router.get_integrations_router import get_integrations


class TestGetIntegrations(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = SimpleNamespace(user_id=uuid4(), organization_id=uuid4())
        self.payload = SimpleNamespace(
            user_id=uuid4(),
            organization_id=uuid4(),
        )
        self.connector = object()
        self.cache_service = SimpleNamespace(
            get_integrations=AsyncMock(),
            set_integrations=AsyncMock(),
        )

    @patch('api.router.get_integrations_router.IntegrationProfileResponse')
    @patch('api.router.get_integrations_router.IntegrationRepository')
    @patch('api.router.get_integrations_router.get_current_identity')
    async def test_returns_cached_response(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_resp_cls,
    ):
        mock_get_current_identity.return_value = self.identity

        cached = [{'from': 'cache'}]
        self.cache_service.get_integrations.return_value = cached

        result = await get_integrations(
            self.payload, connector=self.connector, cache_service=self.cache_service
        )

        self.assertIs(result, cached)
        self.cache_service.get_integrations.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        mock_repo_cls.assert_not_called()
        mock_resp_cls.assert_not_called()
        self.cache_service.set_integrations.assert_not_awaited()

    @patch('api.router.get_integrations_router.IntegrationProfileResponse')
    @patch('api.router.get_integrations_router.IntegrationRepository')
    @patch('api.router.get_integrations_router.get_current_identity')
    async def test_cache_miss_builds_list_and_sets_cache(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_resp_cls,
    ):
        mock_get_current_identity.return_value = self.identity
        self.cache_service.get_integrations.return_value = None

        profiles = [
            SimpleNamespace(
                id=uuid4(),
                service_type='postgres',
                connection_name='analytics',
                database_name='db_analytics',
                auth_method='password',
                autosync_on=True,
            ),
            SimpleNamespace(
                id=uuid4(),
                service_type='mysql',
                connection_name='bi',
                database_name='bi_db',
                auth_method='password',
                autosync_on=False,
            ),
        ]
        repo = Mock()
        repo.get_user_integration_profiles = AsyncMock(return_value=profiles)
        mock_repo_cls.return_value = repo

        mock_resp_cls.side_effect = lambda **kwargs: kwargs

        result = await get_integrations(
            self.payload, connector=self.connector, cache_service=self.cache_service
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(profiles))
        self.assertEqual(result[0]['id'], profiles[0].id)
        self.assertEqual(result[0]['service_type'], profiles[0].service_type)
        self.assertEqual(result[0]['connection_name'], profiles[0].connection_name)
        self.assertEqual(result[0]['database_name'], profiles[0].database_name)
        self.assertEqual(result[0]['auth_method'], profiles[0].auth_method)
        self.assertEqual(result[0]['autosync_on'], profiles[0].autosync_on)

        self.cache_service.get_integrations.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        repo.get_user_integration_profiles.assert_awaited_once_with(
            user_id=self.payload.user_id,
            organization_id=self.payload.organization_id,
        )
        self.assertEqual(mock_resp_cls.call_count, len(profiles))

        self.cache_service.set_integrations.assert_awaited_once_with(
            user_identity=self.identity,
            request=self.payload,
            response=result,
        )

    @patch('api.router.get_integrations_router.IntegrationProfileResponse')
    @patch('api.router.get_integrations_router.IntegrationRepository')
    @patch('api.router.get_integrations_router.get_current_identity')
    async def test_integration_get_failed_raises_424_and_no_cache_set(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_resp_cls,
    ):
        mock_get_current_identity.return_value = self.identity
        self.cache_service.get_integrations.return_value = None

        from database.exceptions import IntegrationGetFailed

        class DummyGetFailed(IntegrationGetFailed):
            def __str__(self):
                return 'db fail'

        repo = Mock()
        repo.get_user_integration_profiles = AsyncMock(side_effect=DummyGetFailed())
        mock_repo_cls.return_value = repo

        with self.assertRaises(HTTPException) as ctx:
            await get_integrations(
                self.payload, connector=self.connector, cache_service=self.cache_service
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertEqual(exc.detail, {'message': 'Database error: db fail'})
        mock_resp_cls.assert_not_called()
        self.cache_service.set_integrations.assert_not_awaited()

    @patch('api.router.get_integrations_router.IntegrationProfileResponse')
    @patch('api.router.get_integrations_router.IntegrationRepository')
    @patch('api.router.get_integrations_router.get_current_identity')
    async def test_unexpected_error_raises_500_and_no_cache_set(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_resp_cls,
    ):
        mock_get_current_identity.return_value = self.identity
        self.cache_service.get_integrations.return_value = None

        repo = Mock()
        repo.get_user_integration_profiles = AsyncMock(side_effect=RuntimeError('boom'))
        mock_repo_cls.return_value = repo

        with self.assertRaises(HTTPException) as ctx:
            await get_integrations(
                self.payload, connector=self.connector, cache_service=self.cache_service
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(exc.detail, {'message': 'Unexpected error: boom'})
        mock_resp_cls.assert_not_called()
        self.cache_service.set_integrations.assert_not_awaited()
