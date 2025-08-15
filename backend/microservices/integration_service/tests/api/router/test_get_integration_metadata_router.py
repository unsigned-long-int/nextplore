import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status

from api.router.get_integration_metadata_router import get_integration


class TestGetIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = SimpleNamespace(user_id=uuid4(), organization_id=uuid4())
        self.payload = SimpleNamespace(
            user_id=uuid4(),
            organization_id=uuid4(),
            integration_id=uuid4(),
        )
        self.connector = object()
        self.cache_service = SimpleNamespace(
            get_integration_metadata=AsyncMock(),
            set_integration_metadata=AsyncMock(),
        )

    @patch('api.router.get_integration_metadata_router.IntegrationMetadataResponse')
    @patch('api.router.get_integration_metadata_router.decrypt_integration')
    @patch('api.router.get_integration_metadata_router.IntegrationRepository')
    @patch('api.router.get_integration_metadata_router.get_current_identity')
    async def test_returns_cached_response(
        self,
        mock_get_current_identity,
        repo_cls,
        decrypt_mock,
        response_cls,
    ):
        mock_get_current_identity.return_value = self.identity

        cached = {'from': 'cache'}
        self.cache_service.get_integration_metadata.return_value = cached

        result = await get_integration(
            self.payload,
            connector=self.connector,
            cache_service=self.cache_service
        )

        self.assertIs(result, cached)
        self.cache_service.get_integration_metadata.assert_awaited_once_with(
            user_identity=self.identity,
            request=self.payload,
        )
        repo_cls.assert_not_called()
        decrypt_mock.assert_not_called()
        response_cls.assert_not_called()
        self.cache_service.set_integration_metadata.assert_not_awaited()

    @patch('api.router.get_integration_metadata_router.IntegrationMetadataResponse')
    @patch('api.router.get_integration_metadata_router.decrypt_integration')
    @patch('api.router.get_integration_metadata_router.IntegrationRepository')
    @patch('api.router.get_integration_metadata_router.get_current_identity')
    async def test_cache_miss_builds_response_and_sets_cache(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_decrypt,
        mock_response_cls,
    ):
        mock_get_current_identity.return_value = self.identity
        self.cache_service.get_integration_metadata.return_value = None

        repo = Mock()
        encrypted = object()
        repo.get_integration = AsyncMock(return_value=encrypted)
        mock_repo_cls.return_value = repo

        decrypted = SimpleNamespace(
            service_type='postgres',
            auth_method='password',
            connection_name='analytics',
            host='db.local',
            port=5432,
            database_name='analytics_db',
            username='alice',
            password='secret',
            kerberos_principal=None,
            windows_domain=None,
            extra_options={'sslmode': 'require'},
            autosync_on=True,
        )
        mock_decrypt.return_value = decrypted

        built_response = {'service_type': 'postgres', 'built': True}
        mock_response_cls.side_effect = lambda **kwargs: built_response

        result = await get_integration(
            self.payload,
            connector=self.connector,
            cache_service=self.cache_service
        )

        self.assertIs(result, built_response)

        self.cache_service.get_integration_metadata.assert_awaited_once_with(
            user_identity=self.identity, request=self.payload
        )
        repo.get_integration.assert_awaited_once_with(
            user_id=self.payload.user_id,
            organization_id=self.payload.organization_id,
            integration_id=self.payload.integration_id,
        )
        mock_decrypt.assert_called_once_with(encrypted)
        mock_response_cls.assert_called_once_with(
            service_type=decrypted.service_type,
            auth_method=decrypted.auth_method,
            connection_name=decrypted.connection_name,
            host=decrypted.host,
            port=decrypted.port,
            database_name=decrypted.database_name,
            username=decrypted.username,
            password=decrypted.password,
            kerberos_principal=decrypted.kerberos_principal,
            windows_domain=decrypted.windows_domain,
            extra_options=decrypted.extra_options,
            autosync_on=decrypted.autosync_on,
        )
        self.cache_service.set_integration_metadata.assert_awaited_once_with(
            user_identity=self.identity,
            request=self.payload,
            response=built_response,
        )

    @patch('api.router.get_integration_metadata_router.decrypt_integration')
    @patch('api.router.get_integration_metadata_router.IntegrationRepository')
    @patch('api.router.get_integration_metadata_router.get_current_identity')
    async def test_integration_get_failed_raises_424(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_decrypt,
    ):
        mock_get_current_identity.return_value = self.identity
        self.cache_service.get_integration_metadata.return_value = None

        from database.exceptions import IntegrationGetFailed

        class DummyGetFailed(IntegrationGetFailed):
            def __str__(self):
                return 'not found'

        repo = Mock()
        repo.get_integration = AsyncMock(side_effect=DummyGetFailed())
        mock_repo_cls.return_value = repo

        with self.assertRaises(HTTPException) as ctx:
            await get_integration(
                self.payload,
                connector=self.connector,
                cache_service=self.cache_service
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertEqual(exc.detail, {'message': 'Database error: not found'})

        mock_decrypt.assert_not_called()
        self.cache_service.set_integration_metadata.assert_not_awaited()

    @patch('api.router.get_integration_metadata_router.IntegrationMetadataResponse')
    @patch('api.router.get_integration_metadata_router.decrypt_integration')
    @patch('api.router.get_integration_metadata_router.IntegrationRepository')
    @patch('api.router.get_integration_metadata_router.get_current_identity')
    async def test_unexpected_exception_raises_500(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_decrypt,
        mock_response_cls,
    ):
        mock_get_current_identity.return_value = self.identity
        self.cache_service.get_integration_metadata.return_value = None

        repo = Mock()
        repo.get_integration = AsyncMock(return_value=object())
        mock_repo_cls.return_value = repo

        mock_decrypt.side_effect = RuntimeError('boom')

        with self.assertRaises(HTTPException) as ctx:
            await get_integration(
                self.payload,
                connector=self.connector,
                cache_service=self.cache_service
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(exc.detail, {'message': 'Unexpected error: boom'})

        self.cache_service.set_integration_metadata.assert_not_awaited()
        mock_response_cls.assert_not_called()
