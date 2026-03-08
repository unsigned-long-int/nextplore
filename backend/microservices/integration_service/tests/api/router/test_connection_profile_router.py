import unittest
from uuid import uuid4
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from svc_integration_contracts.models import (
    IntegrationConnectionProfile,
    DB,
    Auth,
    Cloud
)

from integration_service.domain.models.integration import Integration
from integration_service.cache import get_cache_service
from integration_service.api.router.connection_profile_router import router
from integration_service.api.dependencies import get_backend_connector
from integration_service.database.exceptions import IntegrationGetFailed, SecretsGetFailed


class TestConnectionProfileRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.cache_mock = AsyncMock()
        self.db_connector_mock = AsyncMock()
        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_backend_connector: lambda: self.db_connector_mock,
        }

        self.org_id = uuid4()
        self.user_id = uuid4()
        self.integration_id = uuid4()

        self.integration = Integration(
            id=self.integration_id,
            organization_id=self.org_id,
            user_id=self.user_id,
            auth=Auth.secret,
            cloud=Cloud.azure,
            db=DB.sqlserver,
            connection_name='test-connection',
            host='localhost',
            database_name='test-database',
            kek_kid='azure-kek-kid',
            port=1433,
            warehouse='test-warehouse',
            tenant_id='test-tenant_id',
            client_id='test-client-id',
            region='test-region',
            azure_cert_kid=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=True
        )

        self.secrets = [{'k': 'v'}]

    def _url(self, org_id=None, user_id=None, integration_id=None) -> str:
        return (
            f'/v1/integration/organizations/{org_id or self.org_id}/'
            f'users/{user_id or self.user_id}/integrations/{integration_id or self.integration_id}/connection-profile'
        )

    @patch('integration_service.api.router.connection_profile_router.get_current_identity')
    def test_returns_cached_profile(self, get_current_identity_mock):
        identity = MagicMock()
        identity.organization_id = self.org_id
        identity.user_id = self.user_id
        get_current_identity_mock.return_value = identity

        cached = IntegrationConnectionProfile(
            auth=self.integration.auth,
            cloud=self.integration.cloud,
            db=self.integration.db,
            host=self.integration.host,
            database_name=self.integration.database_name,
            port=self.integration.port,
            warehouse=self.integration.warehouse,
            username='cached_user',
            password='cached_pwd',
            client_secret='cached_secret',
            aws_external_id='cached_ext',
            aws_role_arn='cached_arn',
            snowflake_private_key=None,
            azure_cert_kid=self.integration.azure_cert_kid,
            tenant_id=self.integration.tenant_id,
            client_id=self.integration.client_id,
            region=self.integration.region,
        )
        self.cache_mock.get_connection_profile.return_value = cached

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), cached.model_dump(mode='json'))

        self.cache_mock.get_connection_profile.assert_awaited_once_with(
            user_identity=identity, integration_id=self.integration_id
        )
        self.cache_mock.set_connection_profile.assert_not_awaited()


    @patch('integration_service.api.router.connection_profile_router.AzureCryptoClient')
    @patch('integration_service.api.router.connection_profile_router.decrypt_secret')
    @patch('integration_service.api.router.connection_profile_router.IntegrationRepository')
    @patch('integration_service.api.router.connection_profile_router.get_current_identity')
    def test_loads_from_repo_decrypts_and_sets_cache(
        self,
        get_current_identity_mock,
        repo_cls_mock,
        decrypt_secret_mock,
        azure_crypto_client_cls_mock,
    ):
        identity = MagicMock()
        identity.organization_id = self.org_id
        identity.user_id = self.user_id
        get_current_identity_mock.return_value = identity
        self.cache_mock.get_connection_profile.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_integration.return_value = self.integration
        repo_instance.get_secrets.return_value = self.secrets
        repo_cls_mock.return_value = repo_instance

        decrypt_map = {
            'USERNAME': 'user1',
            'PASSWORD': 'pwd1',
            'CLIENT_SECRET': 'client-secret-1',
            'AWS_EXTERNAL_ID': 'ext-123',
            'AWS_ROLE_ARN': 'arn:aws:iam::123:role/role1',
            'SNOWFLAKE_PRIVATE_KEY': None,
        }

        def _decrypt(secret_type, secrets, client):
            return decrypt_map[secret_type.name]

        decrypt_secret_mock.side_effect = _decrypt

        azure_client_instance = MagicMock()
        azure_crypto_client_cls_mock.return_value = azure_client_instance

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)

        azure_crypto_client_cls_mock.assert_called_once_with(self.integration.kek_kid)

        repo_cls_mock.assert_called_once_with(self.db_connector_mock)
        repo_instance.get_integration.assert_awaited_once_with(
            user_id=identity.user_id,
            organization_id=identity.organization_id,
            integration_id=self.integration_id,
        )
        repo_instance.get_secrets.assert_awaited_once_with(
            user_id=identity.user_id,
            organization_id=identity.organization_id,
            integration_id=self.integration_id,
        )

        expected = IntegrationConnectionProfile(
            auth=self.integration.auth,
            cloud=self.integration.cloud,
            db=self.integration.db,
            host=self.integration.host,
            database_name=self.integration.database_name,
            port=self.integration.port,
            warehouse=self.integration.warehouse,
            username=decrypt_map['USERNAME'],
            password=decrypt_map['PASSWORD'],
            client_secret=decrypt_map['CLIENT_SECRET'],
            aws_external_id=decrypt_map['AWS_EXTERNAL_ID'],
            aws_role_arn=decrypt_map['AWS_ROLE_ARN'],
            snowflake_private_key=decrypt_map['SNOWFLAKE_PRIVATE_KEY'],
            azure_cert_kid=self.integration.azure_cert_kid,
            tenant_id=self.integration.tenant_id,
            client_id=self.integration.client_id,
            region=self.integration.region,
        )
        self.assertEqual(resp.json(), expected.model_dump(mode='json'))

        self.cache_mock.set_connection_profile.assert_awaited_once()
        kwargs = self.cache_mock.set_connection_profile.await_args.kwargs
        self.assertIs(kwargs['user_identity'], identity)
        self.assertEqual(kwargs['integration_id'], self.integration_id)
        self.assertIsInstance(kwargs['response'], IntegrationConnectionProfile)
        self.assertEqual(kwargs['response'].model_dump(mode='json'), expected.model_dump(mode='json'))

        self.assertEqual(decrypt_secret_mock.call_count, 6)
        for _, call_kwargs in decrypt_secret_mock.call_args_list:
            self.assertIs(call_kwargs.get('referenced_image_ids', None), None)  # defensive no-op
        for args, _ in decrypt_secret_mock.call_args_list:
            self.assertIs(args[1], self.secrets)
            self.assertIs(args[2], azure_client_instance)


    @patch('integration_service.api.router.connection_profile_router.get_current_identity')
    def test_forbidden_when_identity_mismatch(self, get_current_identity_mock):
        identity = MagicMock()
        identity.organization_id = uuid4()
        identity.user_id = uuid4()
        get_current_identity_mock.return_value = identity

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json(), {'detail': {'message': 'Forbidden'}})
        self.cache_mock.get_connection_profile.assert_not_called()


    @patch('integration_service.api.router.connection_profile_router.IntegrationRepository')
    @patch('integration_service.api.router.connection_profile_router.get_current_identity')
    def test_integration_get_failed_returns_424(self, get_current_identity_mock, repo_cls_mock):
        identity = MagicMock()
        identity.organization_id = self.org_id
        identity.user_id = self.user_id
        get_current_identity_mock.return_value = identity
        self.cache_mock.get_connection_profile.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_integration.side_effect = IntegrationGetFailed('nope')
        repo_instance.get_secrets.return_value = self.secrets
        repo_cls_mock.return_value = repo_instance

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 424)
        self.assertIn('Database error: nope', resp.text)

    @patch('integration_service.api.router.connection_profile_router.IntegrationRepository')
    @patch('integration_service.api.router.connection_profile_router.get_current_identity')
    def test_secrets_get_failed_returns_424(self, get_current_identity_mock, repo_cls_mock):
        identity = MagicMock()
        identity.organization_id = self.org_id
        identity.user_id = self.user_id
        get_current_identity_mock.return_value = identity
        self.cache_mock.get_connection_profile.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_integration.return_value = self.integration
        repo_instance.get_secrets.side_effect = SecretsGetFailed('no-secrets')
        repo_cls_mock.return_value = repo_instance

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 424)
        self.assertIn('Database error: no-secrets', resp.text)

    @patch('integration_service.api.router.connection_profile_router.IntegrationRepository')
    @patch('integration_service.api.router.connection_profile_router.get_current_identity')
    def test_unexpected_error_returns_500(self, get_current_identity_mock, repo_cls_mock):
        identity = MagicMock()
        identity.organization_id = self.org_id
        identity.user_id = self.user_id
        get_current_identity_mock.return_value = identity
        self.cache_mock.get_connection_profile.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_integration.side_effect = RuntimeError('boom')
        repo_cls_mock.return_value = repo_instance

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 500)
        self.assertIn('Unexpected error: boom', resp.text)
