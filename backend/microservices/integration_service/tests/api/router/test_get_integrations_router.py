import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from api.router.get_integrations_router import get_integrations


class TestGetIntegrations(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = SimpleNamespace(user_id=uuid4(), organization_id=uuid4())
        self.payload = SimpleNamespace(
            user_id=uuid4(),
            organization_id=uuid4(),
        )
        self.connector = object()

    @patch('api.router.get_integrations_router.integration_service_cache')
    @patch('api.router.get_integrations_router.IntegrationProfileResponse')
    @patch('api.router.get_integrations_router.IntegrationRepository')
    @patch('api.router.get_integrations_router.get_current_identity')
    async def test_returns_cached_response(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_resp_cls,
        mock_cache,
    ):
        mock_get_current_identity.return_value = self.identity

        cached = [{'from': 'cache'}]
        mock_cache.get_integrations = AsyncMock(return_value=cached)
        mock_cache.set_integrations = AsyncMock()

        result = await get_integrations(self.payload, connector=self.connector)

        self.assertIs(result, cached)
        mock_cache.get_integrations.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        mock_repo_cls.assert_not_called()
        mock_resp_cls.assert_not_called()
        mock_cache.set_integrations.assert_not_awaited()

    @patch('api.router.get_integrations_router.integration_service_cache')
    @patch('api.router.get_integrations_router.IntegrationProfileResponse')
    @patch('api.router.get_integrations_router.IntegrationRepository')
    @patch('api.router.get_integrations_router.get_current_identity')
    async def test_cache_miss_builds_list_and_sets_cache(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_resp_cls,
        mock_cache,
    ):
        mock_get_current_identity.return_value = self.identity
        mock_cache.get_integrations = AsyncMock(return_value=None)
        mock_cache.set_integrations = AsyncMock()

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

        result = await get_integrations(self.payload, connector=self.connector)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(profiles))
        self.assertEqual(result[0]['id'], profiles[0].id)
        self.assertEqual(result[0]['service_type'], profiles[0].service_type)
        self.assertEqual(result[0]['connection_name'], profiles[0].connection_name)
        self.assertEqual(result[0]['database_name'], profiles[0].database_name)
        self.assertEqual(result[0]['auth_method'], profiles[0].auth_method)
        self.assertEqual(result[0]['autosync_on'], profiles[0].autosync_on)

        mock_cache.get_integrations.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        repo.get_user_integration_profiles.assert_awaited_once_with(
            user_id=self.payload.user_id,
            organization_id=self.payload.organization_id,
        )
        self.assertEqual(mock_resp_cls.call_count, len(profiles))

        mock_cache.set_integrations.assert_awaited_once_with(
            user_identity=self.identity,
            request=self.payload,
            response=result,
        )

    @patch('api.router.get_integrations_router.integration_service_cache')
    @patch('api.router.get_integrations_router.IntegrationProfileResponse')
    @patch('api.router.get_integrations_router.IntegrationRepository')
    @patch('api.router.get_integrations_router.get_current_identity')
    async def test_repo_error_propagates_and_no_cache_set(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_resp_cls,
        mock_cache,
    ):
        mock_get_current_identity.return_value = self.identity
        mock_cache.get_integrations = AsyncMock(return_value=None)
        mock_cache.set_integrations = AsyncMock()

        repo = Mock()
        repo.get_user_integration_profiles = AsyncMock(side_effect=RuntimeError('db fail'))
        mock_repo_cls.return_value = repo

        with self.assertRaises(RuntimeError) as ctx:
            await get_integrations(self.payload, connector=self.connector)
        self.assertEqual(str(ctx.exception), 'db fail')

        mock_resp_cls.assert_not_called()
        mock_cache.set_integrations.assert_not_awaited()
