import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from pydantic import SecretStr

from svc_integration_contracts.models import (
    IntegrationCreateRequest,
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
    IntegrationDeleteFailed
)
from integration_service.database.repositories import IntegrationRepository
from integration_service.domain.models.integration import IntegrationCreate
from integration_service.domain.models.secret import IntegrationSecret, SecretType
from integration_service.services.integration import IntegrationService


class TestIntegrationService(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_repo = AsyncMock(spec=IntegrationRepository)
        self.mock_bus = AsyncMock()
        self.mock_cache_service = MagicMock(spec=CacheService)
        self.mock_cache_service.cache = AsyncMock()
        self.mock_crypto_client = MagicMock()
        self.mock_crypto_client_factory = MagicMock(return_value=self.mock_crypto_client)

        self.service = IntegrationService(
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
            host='test.database.windows.net',
            database_name='testdb',
            kek_kid='https://vault.azure.net/keys/test-key/version',
            port=5432,
            client_secret=SecretStr('secret123')
        )

        self.mock_integration_create = MagicMock(spec=IntegrationCreate)
        self.mock_secrets = {
            SecretType.SECRET: MagicMock(spec=IntegrationSecret)
        }

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
    @patch('integration_service.services.integration.integration_service.logger')
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
        self.assertIn('Create integration failed', log_call[0][0])
        self.assertEqual(log_call[1]['exc_info'], True)

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
    @patch('integration_service.services.integration.integration_service.logger')
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
        self.assertIn('Create integration failed', log_call[0][0])

        extra_data = log_call[1]['extra']
        self.assertEqual(extra_data['org_id'], self.organization_id)
        self.assertEqual(extra_data['user_id'], self.user_id)
        self.assertEqual(extra_data['error_type'], 'SecretsCreateFailed')

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
    @patch('integration_service.services.integration.integration_service.logger')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
    @patch('integration_service.services.integration.integration_service.logger')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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

    @patch('integration_service.services.integration.integration_service.logger')
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

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
    async def test_multiple_secrets_types_handled(
            self,
            mock_secrets_from_dto,
            mock_integration_from_dto
    ):
        mock_integration_from_dto.return_value = self.mock_integration_create
        multiple_secrets = {
            SecretType.SECRET: MagicMock(spec=IntegrationSecret),
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
        self.assertIn(SecretType.SECRET, secrets_arg)
        self.assertIn(SecretType.PASSWORD, secrets_arg)


class TestIntegrationServiceEdgeCases(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_repo = AsyncMock(spec=IntegrationRepository)
        self.mock_bus = AsyncMock()
        self.mock_cache_service = MagicMock(spec=CacheService)
        self.mock_cache_service.cache = AsyncMock()
        self.mock_crypto_client_factory = MagicMock()

        self.service = IntegrationService(
            repo=self.mock_repo,
            bus=self.mock_bus,
            cache_service=self.mock_cache_service,
            crypto_client_factory=self.mock_crypto_client_factory
        )

    @patch('integration_service.services.integration.integration_service.integration_create_from_dto')
    @patch('integration_service.services.integration.integration_service.secrets_from_dto')
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
