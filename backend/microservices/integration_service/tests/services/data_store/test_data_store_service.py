import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from pydantic import SecretStr

from svc_integration_contracts.models import (
    IntegrationCreateRequest,
    IntegrationUpdateRequest,
    Auth,
    DB,
    Cloud
)
from kafka_messaging.events.integration_service import IntegrationCreated

from integration_service.api.context import UserIdentity
from integration_service.cache import CacheService
from integration_service.database.exceptions import (
    IntegrationCreateFailed,
    SecretsCreateFailed,
    IntegrationDeleteFailed,
    IntegrationUpdateFailed,
    KekKidGetFailed
)
from integration_service.database.repositories import DataStoreRepository
from integration_service.domain.models.integration import IntegrationCreate, IntegrationUpdate
from integration_service.domain.models.secret import IntegrationSecret, SecretType
from integration_service.services.data_store import DataStoreService


class TestIntegrationServiceCreate(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_repo = AsyncMock(spec=DataStoreRepository)
        self.mock_bus = AsyncMock()
        self.mock_cache_service = MagicMock(spec=CacheService)
        self.mock_cache_service.cache = AsyncMock()
        self.mock_crypto_client = MagicMock()
        self.mock_crypto_client_factory = MagicMock(return_value=self.mock_crypto_client)

        self.service = DataStoreService(
            repo=self.mock_repo,
            bus=self.mock_bus,
            cache_service=self.mock_cache_service,
            crypto_client_factory=self.mock_crypto_client_factory
        )

        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.integration_id = uuid4()

        self.user_identity = UserIdentity(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.payload = IntegrationCreateRequest(
            auth=Auth.iam,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name='test-connection',
            descr='test-descr',
            host='test.database.windows.net',
            database_name='testdb',
            kek_kid='https://vault.azure.net/keys/test-key/version',
            port=5432,
            client_secret=SecretStr('secret123')
        )

        self.mock_integration_create = MagicMock(spec=IntegrationCreate)
        self.mock_secrets = {
            SecretType.CLIENT_SECRET: MagicMock(spec=IntegrationSecret)
        }

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_create_integration_success(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id

        await self.service.create_integration(
            user_identity=self.user_identity,
            payload=self.payload
        )

        mock_integration_from_dto.assert_called_once_with(self.payload)

        self.mock_repo.create_integration.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            integration_create=self.mock_integration_create
        )

        self.mock_crypto_client_factory.assert_called_once_with(self.payload.kek_kid)

        mock_secrets_from_dto.assert_called_once_with(
            organization_id=self.organization_id,
            integration_id=self.integration_id,
            user_id=self.user_id,
            payload=self.payload,
            crypto_client=self.mock_crypto_client
        )

        self.mock_repo.create_secrets.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            secrets=self.mock_secrets
        )

        self.mock_bus.publish.assert_called_once()
        published_event = self.mock_bus.publish.call_args[0][0]
        self.assertIsInstance(published_event, IntegrationCreated)
        self.assertEqual(published_event.user_id, self.user_id)
        self.assertEqual(published_event.organization_id, self.organization_id)
        self.assertEqual(published_event.integration_id, self.integration_id)

        self.mock_cache_service.cache.delete_by_prefix.assert_called_once_with(
            self.organization_id,
            self.user_id
        )

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_create_integration_calls_in_correct_order(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id

        call_order = []

        async def track_create_integration(*args, **kwargs):
            call_order.append('create_integration')
            return self.integration_id

        async def track_create_secrets(*args, **kwargs):
            call_order.append('create_secrets')

        async def track_publish(*args, **kwargs):
            call_order.append('publish_event')

        async def track_cache_delete(*args, **kwargs):
            call_order.append('cache_delete')

        self.mock_repo.create_integration.side_effect = track_create_integration
        self.mock_repo.create_secrets.side_effect = track_create_secrets
        self.mock_bus.publish.side_effect = track_publish
        self.mock_cache_service.cache.delete_by_prefix.side_effect = track_cache_delete

        await self.service.create_integration(
            user_identity=self.user_identity,
            payload=self.payload
        )

        expected_order = [
            'create_integration',
            'create_secrets',
            'publish_event',
            'cache_delete'
        ]
        self.assertEqual(call_order, expected_order)

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_integration_create_failed_triggers_compensation(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        self.mock_repo.create_integration.side_effect = IntegrationCreateFailed(
            'Database error'
        )

        with self.assertRaises(IntegrationCreateFailed):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        self.mock_repo.delete_integration.assert_not_called()

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_secrets_create_failed_triggers_compensation(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed(
            'Secret encryption failed'
        )

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        self.mock_repo.delete_integration.assert_called_once_with(
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_id=self.integration_id
        )

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_unexpected_error_triggers_compensation(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id
        self.mock_repo.create_secrets.side_effect = Exception('Unexpected error')

        with self.assertRaises(Exception):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        self.mock_repo.delete_integration.assert_called_once_with(
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_id=self.integration_id
        )

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    @patch('integration_service.services.data_store.integration_service.logger')
    async def test_integration_create_failed_logs_error(
            self,
            mock_logger,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        error = IntegrationCreateFailed('Database error')
        self.mock_repo.create_integration.side_effect = error

        with self.assertRaises(IntegrationCreateFailed):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        mock_logger.error.assert_called()
        log_call = mock_logger.error.call_args
        self.assertIn('Create data_store failed', log_call[0][0])
        self.assertEqual(log_call[1]['exc_info'], True)

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    @patch('integration_service.services.data_store.integration_service.logger')
    async def test_secrets_create_failed_logs_error(
            self,
            mock_logger,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id
        error = SecretsCreateFailed('Encryption failed')
        self.mock_repo.create_secrets.side_effect = error

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        mock_logger.error.assert_called()
        log_call = mock_logger.error.call_args
        self.assertIn('Create data_store failed', log_call[0][0])

        extra_data = log_call[1]['extra']
        self.assertEqual(extra_data['org_id'], self.organization_id)
        self.assertEqual(extra_data['user_id'], self.user_id)
        self.assertEqual(extra_data['error_type'], 'SecretsCreateFailed')

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    @patch('integration_service.services.data_store.integration_service.logger')
    async def test_unexpected_error_logs_error(
            self,
            mock_logger,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id
        error = ValueError('Unexpected error')
        self.mock_repo.create_secrets.side_effect = error

        with self.assertRaises(ValueError):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        mock_logger.error.assert_called()
        log_call = mock_logger.error.call_args
        self.assertIn('Unexpected error', log_call[0][0])

        extra_data = log_call[1]['extra']
        self.assertEqual(extra_data['error_type'], 'ValueError')

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_compensation_not_called_when_no_integration_id(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        self.mock_repo.create_integration.side_effect = IntegrationCreateFailed(
            'Database error'
        )

        with self.assertRaises(IntegrationCreateFailed):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        self.mock_repo.delete_integration.assert_not_called()

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    @patch('integration_service.services.data_store.integration_service.logger')
    async def test_compensation_failure_logs_error(
            self,
            mock_logger,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed(
            'Secret encryption failed'
        )
        self.mock_repo.delete_integration.side_effect = IntegrationDeleteFailed(
            'Delete failed'
        )

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        log_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        self.assertTrue(
            any('Compensation failed' in msg for msg in log_calls),
            'Compensation failure should be logged'
        )

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_event_not_published_on_failure(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed(
            'Secret encryption failed'
        )

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        self.mock_bus.publish.assert_not_called()

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_cache_not_invalidated_on_failure(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed(
            'Secret encryption failed'
        )

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_integration(
                user_identity=self.user_identity,
                payload=self.payload
            )

        self.mock_cache_service.cache.delete_by_prefix.assert_not_called()

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_crypto_client_factory_called_with_correct_kek_kid(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id

        kek_kid = 'https://custom-vault.azure.net/keys/custom-key/v1'
        payload_with_custom_kek = IntegrationCreateRequest(
            auth=Auth.iam,
            cloud=Cloud.azure,
            db=DB.mysql,
            connection_name='test-connection',
            descr='test-descr',
            host='test.database.windows.net',
            database_name='testdb',
            kek_kid=kek_kid,
            port=5432,
            client_secret=SecretStr('secret123')
        )

        await self.service.create_integration(
            user_identity=self.user_identity,
            payload=payload_with_custom_kek
        )

        self.mock_crypto_client_factory.assert_called_once_with(kek_kid)

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_secrets_from_dto_called_with_correct_parameters(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_integration.return_value = self.integration_id

        await self.service.create_integration(
            user_identity=self.user_identity,
            payload=self.payload
        )

        mock_secrets_from_dto.assert_called_once_with(
            organization_id=self.organization_id,
            integration_id=self.integration_id,
            user_id=self.user_id,
            payload=self.payload,
            crypto_client=self.mock_crypto_client
        )

    async def test_compensate_delete_integration_returns_none_when_no_id(self):
        result = await self.service._compensate_delete_integration(
            user_identity=self.user_identity,
            integration_id=None
        )

        self.assertIsNone(result)
        self.mock_repo.delete_integration.assert_not_called()

    async def test_compensate_delete_integration_deletes_when_id_exists(self):
        await self.service._compensate_delete_integration(
            user_identity=self.user_identity,
            integration_id=self.integration_id
        )

        self.mock_repo.delete_integration.assert_called_once_with(
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_id=self.integration_id
        )

    @patch('integration_service.services.data_store.integration_service.logger')
    async def test_compensate_delete_integration_logs_failure(self, mock_logger):
        self.mock_repo.delete_integration.side_effect = IntegrationDeleteFailed(
            'Delete failed'
        )

        await self.service._compensate_delete_integration(
            user_identity=self.user_identity,
            integration_id=self.integration_id
        )

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Compensation failed', log_call[0][0])

        extra_data = log_call[1]['extra']
        self.assertEqual(extra_data['org_id'], self.organization_id)
        self.assertEqual(extra_data['user_id'], self.user_id)
        self.assertEqual(extra_data['integration_id'], str(self.integration_id))

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_multiple_secrets_types_handled(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        multiple_secrets = {
            SecretType.CLIENT_SECRET: MagicMock(spec=IntegrationSecret),
            SecretType.PASSWORD: MagicMock(spec=IntegrationSecret),
        }
        mock_secrets_from_dto.return_value = multiple_secrets
        self.mock_repo.create_integration.return_value = self.integration_id

        await self.service.create_integration(
            user_identity=self.user_identity,
            payload=self.payload
        )

        self.mock_repo.create_secrets.assert_called_once()
        secrets_arg = self.mock_repo.create_secrets.call_args[1]['secrets']
        self.assertEqual(len(secrets_arg), 2)
        self.assertIn(SecretType.CLIENT_SECRET, secrets_arg)
        self.assertIn(SecretType.PASSWORD, secrets_arg)


class TestIntegrationServiceUpdate(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_repo = AsyncMock(spec=DataStoreRepository)
        self.mock_bus = AsyncMock()
        self.mock_cache_service = MagicMock(spec=CacheService)
        self.mock_cache_service.cache = AsyncMock()
        self.mock_crypto_client = MagicMock()
        self.mock_crypto_client_factory = MagicMock(return_value=self.mock_crypto_client)

        self.service = DataStoreService(
            repo=self.mock_repo,
            bus=self.mock_bus,
            cache_service=self.mock_cache_service,
            crypto_client_factory=self.mock_crypto_client_factory
        )

        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.integration_id = uuid4()
        self.kek_kid = 'https://vault.azure.net/keys/test-key/version'

        self.user_identity = UserIdentity(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.update_payload = IntegrationUpdateRequest(
            connection_name='updated-connection',
            host='updated.database.windows.net',
            port=5433,
            database_name='updated_db',
            autosync_on=True,
            client_secret=SecretStr('new-secret')
        )

        self.mock_integration_update = MagicMock(spec=IntegrationUpdate)
        self.mock_secrets = {
            SecretType.CLIENT_SECRET: MagicMock(spec=IntegrationSecret)
        }

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_update_integration_success(
            self,
            mock_secrets_from_dto,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.get_kek_kid.return_value = self.kek_kid

        await self.service.update_integration(
            user_identity=self.user_identity,
            integration_id=self.integration_id,
            payload=self.update_payload
        )

        mock_integration_update_from_dto.assert_called_once_with(self.update_payload)

        self.mock_repo.get_kek_kid.assert_called_once_with(
            integration_id=self.integration_id,
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.mock_crypto_client_factory.assert_called_once_with(self.kek_kid)

        mock_secrets_from_dto.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            integration_id=self.integration_id,
            crypto_client=self.mock_crypto_client,
            payload=self.update_payload
        )

        self.mock_repo.update_integration.assert_called_once_with(
            integration_id=self.integration_id,
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_update=self.mock_integration_update,
            secrets=self.mock_secrets
        )

        self.mock_cache_service.cache.delete_by_prefix.assert_called_once_with(
            self.organization_id,
            self.user_id
        )

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_update_integration_calls_in_correct_order(
            self,
            mock_secrets_from_dto,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.get_kek_kid.return_value = self.kek_kid

        call_order = []

        async def track_get_kek_kid(*args, **kwargs):
            call_order.append('get_kek_kid')
            return self.kek_kid

        async def track_update_integration(*args, **kwargs):
            call_order.append('update_integration')

        async def track_cache_delete(*args, **kwargs):
            call_order.append('cache_delete')

        self.mock_repo.get_kek_kid.side_effect = track_get_kek_kid
        self.mock_repo.update_integration.side_effect = track_update_integration
        self.mock_cache_service.cache.delete_by_prefix.side_effect = track_cache_delete

        await self.service.update_integration(
            user_identity=self.user_identity,
            integration_id=self.integration_id,
            payload=self.update_payload
        )

        expected_order = ['get_kek_kid', 'update_integration', 'cache_delete']
        self.assertEqual(call_order, expected_order)

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    async def test_update_integration_raises_kek_kid_get_failed(
            self,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        self.mock_repo.get_kek_kid.side_effect = KekKidGetFailed('KEK KID not found')

        with self.assertRaises(KekKidGetFailed):
            await self.service.update_integration(
                user_identity=self.user_identity,
                integration_id=self.integration_id,
                payload=self.update_payload
            )

        self.mock_repo.update_integration.assert_not_called()
        self.mock_cache_service.cache.delete_by_prefix.assert_not_called()

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_update_integration_raises_integration_update_failed(
            self,
            mock_secrets_from_dto,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.get_kek_kid.return_value = self.kek_kid
        self.mock_repo.update_integration.side_effect = IntegrationUpdateFailed(
            'Update failed'
        )

        with self.assertRaises(IntegrationUpdateFailed):
            await self.service.update_integration(
                user_identity=self.user_identity,
                integration_id=self.integration_id,
                payload=self.update_payload
            )

        self.mock_cache_service.cache.delete_by_prefix.assert_not_called()

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_update_integration_raises_unexpected_error(
            self,
            mock_secrets_from_dto,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.get_kek_kid.return_value = self.kek_kid
        self.mock_repo.update_integration.side_effect = RuntimeError('Unexpected error')

        with self.assertRaises(RuntimeError):
            await self.service.update_integration(
                user_identity=self.user_identity,
                integration_id=self.integration_id,
                payload=self.update_payload
            )

        self.mock_cache_service.cache.delete_by_prefix.assert_not_called()

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    @patch('integration_service.services.data_store.integration_service.logger')
    async def test_update_integration_logs_database_error(
            self,
            mock_logger,
            mock_secrets_from_dto,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.get_kek_kid.return_value = self.kek_kid
        error = IntegrationUpdateFailed('Database error')
        self.mock_repo.update_integration.side_effect = error

        with self.assertRaises(IntegrationUpdateFailed):
            await self.service.update_integration(
                user_identity=self.user_identity,
                integration_id=self.integration_id,
                payload=self.update_payload
            )

        mock_logger.error.assert_called()
        log_call = mock_logger.error.call_args
        self.assertIn('Update data_store failed', log_call[0][0])
        self.assertEqual(log_call[1]['exc_info'], True)

        extra_data = log_call[1]['extra']
        self.assertEqual(extra_data['org_id'], self.organization_id)
        self.assertEqual(extra_data['user_id'], self.user_id)
        self.assertEqual(extra_data['integration_id'], str(self.integration_id))
        self.assertEqual(extra_data['error_type'], 'IntegrationUpdateFailed')

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    @patch('integration_service.services.data_store.integration_service.logger')
    async def test_update_integration_logs_kek_kid_error(
            self,
            mock_logger,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        error = KekKidGetFailed('KEK KID not found')
        self.mock_repo.get_kek_kid.side_effect = error

        with self.assertRaises(KekKidGetFailed):
            await self.service.update_integration(
                user_identity=self.user_identity,
                integration_id=self.integration_id,
                payload=self.update_payload
            )

        mock_logger.error.assert_called()
        log_call = mock_logger.error.call_args
        self.assertIn('Update data_store failed', log_call[0][0])

        extra_data = log_call[1]['extra']
        self.assertEqual(extra_data['error_type'], 'KekKidGetFailed')

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    @patch('integration_service.services.data_store.integration_service.logger')
    async def test_update_integration_logs_unexpected_error(
            self,
            mock_logger,
            mock_secrets_from_dto,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.get_kek_kid.return_value = self.kek_kid
        error = ValueError('Unexpected error')
        self.mock_repo.update_integration.side_effect = error

        with self.assertRaises(ValueError):
            await self.service.update_integration(
                user_identity=self.user_identity,
                integration_id=self.integration_id,
                payload=self.update_payload
            )

        mock_logger.error.assert_called()
        log_call = mock_logger.error.call_args
        self.assertIn('Unexpected error', log_call[0][0])

        extra_data = log_call[1]['extra']
        self.assertEqual(extra_data['error_type'], 'ValueError')

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_update_integration_uses_retrieved_kek_kid(
            self,
            mock_secrets_from_dto,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        mock_secrets_from_dto.return_value = self.mock_secrets
        custom_kek_kid = 'https://custom.vault.com/keys/custom/v2'
        self.mock_repo.get_kek_kid.return_value = custom_kek_kid

        await self.service.update_integration(
            user_identity=self.user_identity,
            integration_id=self.integration_id,
            payload=self.update_payload
        )

        self.mock_crypto_client_factory.assert_called_once_with(custom_kek_kid)

    @patch('integration_service.services.data_store.integration_service.integration_update_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_update_integration_cache_invalidated_only_on_success(
            self,
            mock_secrets_from_dto,
            mock_integration_update_from_dto
    ):
        mock_integration_update_from_dto.return_value = self.mock_integration_update
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.get_kek_kid.return_value = self.kek_kid

        await self.service.update_integration(
            user_identity=self.user_identity,
            integration_id=self.integration_id,
            payload=self.update_payload
        )

        self.mock_cache_service.cache.delete_by_prefix.assert_called_once()
        self.mock_repo.update_integration.assert_called_once()


class TestIntegrationServiceEdgeCases(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_repo = AsyncMock(spec=DataStoreRepository)
        self.mock_bus = AsyncMock()
        self.mock_cache_service = MagicMock(spec=CacheService)
        self.mock_cache_service.cache = AsyncMock()
        self.mock_crypto_client_factory = MagicMock()

        self.service = DataStoreService(
            repo=self.mock_repo,
            bus=self.mock_bus,
            cache_service=self.mock_cache_service,
            crypto_client_factory=self.mock_crypto_client_factory
        )

    @patch('integration_service.services.data_store.integration_service.integration_create_from_dto')
    @patch('integration_service.services.data_store.integration_service.secrets_from_dto')
    async def test_handles_zero_uuid_integration_id(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        zero_uuid = UUID('00000000-0000-0000-0000-000000000000')
        mock_integration_from_dto.return_value = MagicMock()
        mock_secrets_from_dto.return_value = {}
        self.mock_repo.create_integration.return_value = zero_uuid
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed('Failed')

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_integration(
                user_identity=UserIdentity(
                    organization_id=uuid4(),
                    user_id=uuid4()
                ),
                payload=MagicMock()
            )

        self.mock_repo.delete_integration.assert_called_once()