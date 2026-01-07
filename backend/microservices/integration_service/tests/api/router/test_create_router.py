import unittest
from uuid import uuid4
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from integration_service.api.router.create_router import router
from integration_service.api.dependencies import get_backend_connector
from integration_service.api.models.integration_create_request import IntegrationCreateRequest
from integration_service.api.models.auth import Auth
from integration_service.api.models.db import DB
from integration_service.api.models.cloud import Cloud
from integration_service.cache import get_cache_service
from integration_service.database.exceptions import IntegrationCreateFailed, SecretsCreateFailed


class TestCreateRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.cache_mock = AsyncMock()
        self.cache_mock.cache = AsyncMock()
        self.database_backend_connector_mock = AsyncMock()

        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_backend_connector: lambda: self.database_backend_connector_mock,
        }

        self.request = IntegrationCreateRequest(
            auth=Auth.IAM,
            cloud=Cloud.AWS,
            db=DB.POSTGRESQL,
            connection_name='test-connection',
            host='localhost',
            database_name='test-database',
            port=5432
        )

    def _url(self, org_id, user_id) -> str:
        return (
            f'/v1/integration/organizations/{org_id}/'
            f'users/{user_id}/integrations'
        )

    @patch('integration_service.api.router.create_router.get_kafka_message_bus')
    @patch('integration_service.api.router.create_router.AzureCryptoClient')
    @patch('integration_service.api.router.create_router.secrets_from_dto')
    @patch('integration_service.api.router.create_router.integration_create_from_dto')
    @patch('integration_service.api.router.create_router.IntegrationRepository')
    @patch('integration_service.api.router.create_router.get_current_identity')
    def test_creates_integration_successfully(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        integration_create_from_dto_mock,
        secrets_from_dto_mock,
        azure_crypto_client_mock,
        get_kafka_message_bus_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        integration_create_mock = MagicMock()
        integration_create_from_dto_mock.return_value = integration_create_mock

        repo_instance = AsyncMock()
        repo_instance.create_integration.return_value = integration_id
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        crypto_client_mock = MagicMock()
        azure_crypto_client_mock.return_value = crypto_client_mock

        kafka_bus_mock = AsyncMock()
        get_kafka_message_bus_mock.return_value = kafka_bus_mock

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        integration_create_from_dto_mock.assert_called_once_with(self.request)
        repo_instance.create_integration.assert_awaited_once_with(
            organization_id=user_identity_mock.organization_id,
            user_id=user_identity_mock.user_id,
            integration_create=integration_create_mock
        )

        azure_crypto_client_mock.assert_called_once_with(self.request.kek_kid)

        secrets_from_dto_mock.assert_called_once_with(
            organization_id=user_identity_mock.organization_id,
            user_id=user_identity_mock.user_id,
            integration_id=integration_id,
            payload=self.request,
            crypto_client=crypto_client_mock
        )
        repo_instance.create_secrets.assert_awaited_once_with(
            organization_id=user_identity_mock.organization_id,
            user_id=user_identity_mock.user_id,
            secrets=secrets_mock
        )

        kafka_bus_mock.publish.assert_awaited_once()
        published_event = kafka_bus_mock.publish.call_args[0][0]
        self.assertEqual(published_event.user_id, user_identity_mock.user_id)
        self.assertEqual(published_event.organization_id, user_identity_mock.organization_id)
        self.assertEqual(published_event.integration_id, integration_id)

        self.cache_mock.cache.delete_by_prefix.assert_awaited_once_with(
            user_identity_mock.organization_id,
            user_identity_mock.user_id
        )

    @patch('integration_service.api.router.create_router.get_current_identity')
    def test_returns_forbidden_when_org_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_org_id = uuid4()

        response = self.client.post(
            self._url(different_org_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])

    @patch('integration_service.api.router.create_router.get_current_identity')
    def test_returns_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_user_id = uuid4()

        response = self.client.post(
            self._url(user_identity_mock.organization_id, different_user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])

    @patch('integration_service.api.router.create_router.integration_create_from_dto')
    @patch('integration_service.api.router.create_router.IntegrationRepository')
    @patch('integration_service.api.router.create_router.get_current_identity')
    def test_raises_exception_when_integration_create_failed(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        integration_create_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_create_mock = MagicMock()
        integration_create_from_dto_mock.return_value = integration_create_mock

        repo_instance = AsyncMock()
        repo_instance.create_integration.side_effect = IntegrationCreateFailed('Database connection error')
        integration_repo_mock.return_value = repo_instance

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(424, response.status_code)
        self.assertIn('Database error: Database connection error', response.json()['detail']['message'])
        self.cache_mock.cache.delete_by_prefix.assert_not_awaited()

    @patch('integration_service.api.router.create_router.get_kafka_message_bus')
    @patch('integration_service.api.router.create_router.AzureCryptoClient')
    @patch('integration_service.api.router.create_router.secrets_from_dto')
    @patch('integration_service.api.router.create_router.integration_create_from_dto')
    @patch('integration_service.api.router.create_router.IntegrationRepository')
    @patch('integration_service.api.router.create_router.get_current_identity')
    def test_raises_exception_when_secrets_create_failed(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        integration_create_from_dto_mock,
        secrets_from_dto_mock,
        azure_crypto_client_mock,
        get_kafka_message_bus_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        integration_create_mock = MagicMock()
        integration_create_from_dto_mock.return_value = integration_create_mock

        repo_instance = AsyncMock()
        repo_instance.create_integration.return_value = integration_id
        repo_instance.create_secrets.side_effect = SecretsCreateFailed('Secret encryption failed')
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        crypto_client_mock = MagicMock()
        azure_crypto_client_mock.return_value = crypto_client_mock

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(424, response.status_code)
        self.assertIn('Database error: Secret encryption failed', response.json()['detail']['message'])
        self.cache_mock.cache.delete_by_prefix.assert_not_awaited()

    @patch('integration_service.api.router.create_router.integration_create_from_dto')
    @patch('integration_service.api.router.create_router.IntegrationRepository')
    @patch('integration_service.api.router.create_router.get_current_identity')
    def test_raises_exception_when_generic_error(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        integration_create_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_create_mock = MagicMock()
        integration_create_from_dto_mock.return_value = integration_create_mock

        repo_instance = AsyncMock()
        repo_instance.create_integration.side_effect = RuntimeError('Unexpected error')
        integration_repo_mock.return_value = repo_instance

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected error: Unexpected error', response.json()['detail']['message'])
        self.cache_mock.cache.delete_by_prefix.assert_not_awaited()

    @patch('integration_service.api.router.create_router.get_kafka_message_bus')
    @patch('integration_service.api.router.create_router.AzureCryptoClient')
    @patch('integration_service.api.router.create_router.secrets_from_dto')
    @patch('integration_service.api.router.create_router.integration_create_from_dto')
    @patch('integration_service.api.router.create_router.IntegrationRepository')
    @patch('integration_service.api.router.create_router.get_current_identity')
    def test_does_not_publish_kafka_event_when_secrets_fail(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        integration_create_from_dto_mock,
        secrets_from_dto_mock,
        azure_crypto_client_mock,
        get_kafka_message_bus_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        integration_create_mock = MagicMock()
        integration_create_from_dto_mock.return_value = integration_create_mock

        repo_instance = AsyncMock()
        repo_instance.create_integration.return_value = integration_id
        repo_instance.create_secrets.side_effect = SecretsCreateFailed('Secret encryption failed')
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        crypto_client_mock = MagicMock()
        azure_crypto_client_mock.return_value = crypto_client_mock

        kafka_bus_mock = AsyncMock()
        get_kafka_message_bus_mock.return_value = kafka_bus_mock

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(424, response.status_code)

        kafka_bus_mock.publish.assert_not_awaited()

    @patch('integration_service.api.router.create_router.get_kafka_message_bus')
    @patch('integration_service.api.router.create_router.AzureCryptoClient')
    @patch('integration_service.api.router.create_router.secrets_from_dto')
    @patch('integration_service.api.router.create_router.integration_create_from_dto')
    @patch('integration_service.api.router.create_router.IntegrationRepository')
    @patch('integration_service.api.router.create_router.get_current_identity')
    def test_uses_correct_kek_kid_for_crypto_client(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_create_from_dto_mock,
            secrets_from_dto_mock,
            azure_crypto_client_mock,
            get_kafka_message_bus_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        custom_kek_kid = 'custom-kek-12345'
        request_with_custom_kek = IntegrationCreateRequest(
            auth=Auth.IAM,
            cloud=Cloud.AWS,
            db=DB.POSTGRESQL,
            connection_name='test-connection',
            host='localhost',
            database_name='test-database',
            port=5432,
            kek_kid=custom_kek_kid
        )

        integration_id = uuid4()
        integration_create_mock = MagicMock()
        integration_create_from_dto_mock.return_value = integration_create_mock

        repo_instance = AsyncMock()
        repo_instance.create_integration.return_value = integration_id
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        crypto_client_mock = MagicMock()
        azure_crypto_client_mock.return_value = crypto_client_mock

        kafka_bus_mock = AsyncMock()
        get_kafka_message_bus_mock.return_value = kafka_bus_mock

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=request_with_custom_kek.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        azure_crypto_client_mock.assert_called_once_with(custom_kek_kid)
