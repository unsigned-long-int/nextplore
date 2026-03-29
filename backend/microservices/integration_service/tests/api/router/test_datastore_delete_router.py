import unittest
from uuid import uuid4
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from integration_service.api.router.datastore_delete_router import router
from integration_service.api.dependencies import get_backend_connector
from integration_service.cache import get_cache_service
from integration_service.database.exceptions import DataStoreDeleteFailed


class TestDataStoreDeleteRouter(unittest.TestCase):
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

    def _url(self, org_id, user_id, datastore_id) -> str:
        return (
            f'/v1/integration/organizations/{org_id}/'
            f'users/{user_id}/datastores/{datastore_id}'
        )

    @patch('integration_service.api.router.datastore_delete_router.get_kafka_message_bus')
    @patch('integration_service.api.router.datastore_delete_router.DataStoreRepository')
    @patch('integration_service.api.router.datastore_delete_router.get_current_identity')
    def test_deletes_datastore_successfully(
            self,
            get_current_identity_mock,
            datastore_repo_mock,
            get_kafka_message_bus_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        repo_instance = AsyncMock()
        datastore_repo_mock.return_value = repo_instance

        kafka_bus_mock = AsyncMock()
        get_kafka_message_bus_mock.return_value = kafka_bus_mock

        response = self.client.delete(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id
            )
        )

        self.assertEqual(204, response.status_code)

        repo_instance.delete_datastore.assert_awaited_once_with(
            datastore_id=datastore_id,
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id
        )

        kafka_bus_mock.publish.assert_awaited_once()
        published_event = kafka_bus_mock.publish.call_args[0][0]
        self.assertEqual(published_event.user_id, user_identity_mock.user_id)
        self.assertEqual(published_event.organization_id, user_identity_mock.organization_id)
        self.assertEqual(published_event.datastore_id, datastore_id)

        self.cache_mock.cache.delete_by_prefix.assert_awaited_once_with(
            user_identity_mock.organization_id,
            user_identity_mock.user_id
        )

    @patch('integration_service.api.router.datastore_delete_router.get_current_identity')
    def test_returns_forbidden_when_org_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_org_id = uuid4()
        datastore_id = uuid4()

        response = self.client.delete(
            self._url(different_org_id, user_identity_mock.user_id, datastore_id)
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])

    @patch('integration_service.api.router.datastore_delete_router.get_current_identity')
    def test_returns_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_user_id = uuid4()
        datastore_id = uuid4()

        response = self.client.delete(
            self._url(user_identity_mock.organization_id, different_user_id, datastore_id)
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])

    @patch('integration_service.api.router.datastore_delete_router.DataStoreRepository')
    @patch('integration_service.api.router.datastore_delete_router.get_current_identity')
    def test_raises_exception_when_datastore_delete_failed(
        self,
        get_current_identity_mock,
        datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        repo_instance = AsyncMock()
        repo_instance.delete_datastore.side_effect = DataStoreDeleteFailed(
            'data store not found or already deleted'
        )
        datastore_repo_mock.return_value = repo_instance

        response = self.client.delete(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id
            )
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            'Database error: data store not found or already deleted',
            response.json()['detail']['message']
        )
        self.cache_mock.cache.delete_by_prefix.assert_not_awaited()

    @patch('integration_service.api.router.datastore_delete_router.DataStoreRepository')
    @patch('integration_service.api.router.datastore_delete_router.get_current_identity')
    def test_raises_exception_when_generic_error(
        self,
        get_current_identity_mock,
        datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        repo_instance = AsyncMock()
        repo_instance.delete_datastore.side_effect = RuntimeError('Connection timeout')
        datastore_repo_mock.return_value = repo_instance

        response = self.client.delete(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id
            )
        )

        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected error: Connection timeout', response.json()['detail']['message'])
        self.cache_mock.cache.delete_by_prefix.assert_not_awaited()

    @patch('integration_service.api.router.datastore_delete_router.get_kafka_message_bus')
    @patch('integration_service.api.router.datastore_delete_router.DataStoreRepository')
    @patch('integration_service.api.router.datastore_delete_router.get_current_identity')
    def test_does_not_publish_kafka_event_when_delete_fails(
        self,
        get_current_identity_mock,
        datastore_repo_mock,
        get_kafka_message_bus_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        repo_instance = AsyncMock()
        repo_instance.delete_datastore.side_effect = DataStoreDeleteFailed(
            'Foreign key constraint violation'
        )
        datastore_repo_mock.return_value = repo_instance

        kafka_bus_mock = AsyncMock()
        get_kafka_message_bus_mock.return_value = kafka_bus_mock

        response = self.client.delete(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id
            )
        )

        self.assertEqual(424, response.status_code)

        kafka_bus_mock.publish.assert_not_awaited()

    @patch('integration_service.api.router.datastore_delete_router.get_kafka_message_bus')
    @patch('integration_service.api.router.datastore_delete_router.DataStoreRepository')
    @patch('integration_service.api.router.datastore_delete_router.get_current_identity')
    def test_publishes_correct_datastore_id_in_kafka_event(
        self,
        get_current_identity_mock,
        datastore_repo_mock,
        get_kafka_message_bus_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        repo_instance = AsyncMock()
        datastore_repo_mock.return_value = repo_instance

        kafka_bus_mock = AsyncMock()
        get_kafka_message_bus_mock.return_value = kafka_bus_mock

        response = self.client.delete(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id
            )
        )

        self.assertEqual(204, response.status_code)

        kafka_bus_mock.publish.assert_awaited_once()
        published_event = kafka_bus_mock.publish.call_args[0][0]
        self.assertEqual(published_event.datastore_id, datastore_id)

    @patch('integration_service.api.router.datastore_delete_router.get_kafka_message_bus')
    @patch('integration_service.api.router.datastore_delete_router.DataStoreRepository')
    @patch('integration_service.api.router.datastore_delete_router.get_current_identity')
    def test_cache_invalidation_uses_correct_prefix_parameters(
            self,
            get_current_identity_mock,
            datastore_repo_mock,
            get_kafka_message_bus_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        repo_instance = AsyncMock()
        datastore_repo_mock.return_value = repo_instance

        kafka_bus_mock = AsyncMock()
        get_kafka_message_bus_mock.return_value = kafka_bus_mock

        response = self.client.delete(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id
            )
        )

        self.assertEqual(204, response.status_code)

        self.cache_mock.cache.delete_by_prefix.assert_awaited_once_with(
            user_identity_mock.organization_id,
            user_identity_mock.user_id
        )

    @patch('integration_service.api.router.datastore_delete_router.get_kafka_message_bus')
    @patch('integration_service.api.router.datastore_delete_router.DataStoreRepository')
    @patch('integration_service.api.router.datastore_delete_router.get_current_identity')
    def test_deletes_datastore_with_matching_credentials(
        self,
        get_current_identity_mock,
        datastore_repo_mock,
        get_kafka_message_bus_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        repo_instance = AsyncMock()
        datastore_repo_mock.return_value = repo_instance

        kafka_bus_mock = AsyncMock()
        get_kafka_message_bus_mock.return_value = kafka_bus_mock

        response = self.client.delete(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id
            )
        )

        self.assertEqual(204, response.status_code)

        repo_instance.delete_datastore.assert_awaited_once_with(
            datastore_id=datastore_id,
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id
        )