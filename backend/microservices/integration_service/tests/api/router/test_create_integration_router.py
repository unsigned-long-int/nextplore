import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status

from api.router.create_integration_router import create_integration
from database.exceptions import IntegrationCreateFailed


class TestCreateIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = SimpleNamespace(user_id='user-123', organization_id='org-456')
        self.connector = object()

        self.payload_dict = {
            'user_id': 'user-123',
            'organization_id': 'org-456',
            'name': 'My Integration',
            'config': {'k': 'v'},
        }
        self.payload = SimpleNamespace(model_dump=Mock(return_value=self.payload_dict))

        self.cache_service = SimpleNamespace(
            cache=SimpleNamespace(delete_by_prefix=AsyncMock())
        )

    @patch('api.router.create_integration_router.get_kafka_message_bus')
    @patch('api.router.create_integration_router.IntegrationRepository')
    @patch('api.router.create_integration_router.encrypt_integration')
    @patch('api.router.create_integration_router.DecryptedIntegration')
    @patch('api.router.create_integration_router.get_current_identity')
    async def test_success_happy_path(
        self,
        mock_get_current_identity,
        mock_decrypted_integration_cls,
        mock_encrypt_integration,
        mock_repo_cls,
        mock_get_bus,
    ):
        mock_get_current_identity.return_value = self.identity

        mock_decrypted_integration_cls.return_value = SimpleNamespace(**self.payload_dict)

        user_id = uuid4()
        org_id = uuid4()
        encrypted = SimpleNamespace(user_id=user_id, organization_id=org_id)
        mock_encrypt_integration.return_value = encrypted

        integration_id = uuid4()
        repo_instance = Mock()
        repo_instance.create_integration = AsyncMock(return_value=integration_id)
        mock_repo_cls.return_value = repo_instance

        bus = SimpleNamespace(publish=AsyncMock())
        mock_get_bus.return_value = bus

        result = await create_integration(
            self.payload, connector=self.connector, cache_service=self.cache_service
        )
        self.assertIsNone(result)

        mock_decrypted_integration_cls.assert_called_once_with(**self.payload_dict)
        mock_encrypt_integration.assert_called_once_with(mock_decrypted_integration_cls.return_value)

        repo_instance.create_integration.assert_awaited_once_with(
            organization_id=self.identity.organization_id,
            user_id=self.identity.user_id,
            encrypted_integration=encrypted,
        )

        call = getattr(bus.publish, 'await_args', None) or bus.publish.call_args
        event = call.args[0]
        self.assertEqual(getattr(event, 'user_id', None), user_id)
        self.assertEqual(getattr(event, 'organization_id', None), org_id)
        self.assertEqual(getattr(event, 'integration_id', None), integration_id)

        self.cache_service.cache.delete_by_prefix.assert_awaited_once_with(
            self.identity.organization_id, self.identity.user_id
        )

    @patch('api.router.create_integration_router.get_kafka_message_bus')
    @patch('api.router.create_integration_router.IntegrationRepository')
    @patch('api.router.create_integration_router.encrypt_integration')
    @patch('api.router.create_integration_router.DecryptedIntegration')
    @patch('api.router.create_integration_router.get_current_identity')
    async def test_integration_create_failed_raises_424(
        self,
        mock_get_current_identity,
        mock_decrypted_integration_cls,
        mock_encrypt_integration,
        mock_repo_cls,
        mock_get_bus,
    ):
        mock_get_current_identity.return_value = self.identity
        mock_decrypted_integration_cls.return_value = SimpleNamespace(**self.payload_dict)

        user_id = uuid4()
        org_id = uuid4()
        mock_encrypt_integration.return_value = SimpleNamespace(user_id=user_id, organization_id=org_id)

        class DummyCreateFailed(IntegrationCreateFailed):
            def __str__(self):
                return 'boom'

        repo_instance = Mock()
        repo_instance.create_integration = AsyncMock(side_effect=DummyCreateFailed())
        mock_repo_cls.return_value = repo_instance

        mock_get_bus.return_value = SimpleNamespace(publish=AsyncMock())

        with self.assertRaises(HTTPException) as ctx:
            await create_integration(
                self.payload, connector=self.connector, cache_service=self.cache_service
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertEqual(exc.detail, {'message': 'Database error: boom'})

        mock_get_bus.return_value.publish.assert_not_awaited()
        self.cache_service.cache.delete_by_prefix.assert_not_awaited()

    @patch('api.router.create_integration_router.get_kafka_message_bus')
    @patch('api.router.create_integration_router.IntegrationRepository')
    @patch('api.router.create_integration_router.encrypt_integration')
    @patch('api.router.create_integration_router.DecryptedIntegration')
    @patch('api.router.create_integration_router.get_current_identity')
    async def test_unexpected_exception_raises_500(
        self,
        mock_get_current_identity,
        mock_decrypted_integration_cls,
        mock_encrypt_integration,
        mock_repo_cls,
        mock_get_bus,
    ):
        mock_get_current_identity.return_value = self.identity
        mock_decrypted_integration_cls.return_value = SimpleNamespace(**self.payload_dict)

        mock_encrypt_integration.side_effect = RuntimeError('oops')

        repo_instance = Mock()
        repo_instance.create_integration = AsyncMock()
        mock_repo_cls.return_value = repo_instance

        mock_get_bus.return_value = SimpleNamespace(publish=AsyncMock())

        with self.assertRaises(HTTPException) as ctx:
            await create_integration(
                self.payload, connector=self.connector, cache_service=self.cache_service
            )

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(exc.detail, {'message': 'Unexpected error: oops'})

        repo_instance.create_integration.assert_not_awaited()
        mock_get_bus.return_value.publish.assert_not_awaited()
        self.cache_service.cache.delete_by_prefix.assert_not_awaited()
