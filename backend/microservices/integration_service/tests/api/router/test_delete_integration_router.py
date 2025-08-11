import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status

from database.repositories import IntegrationDeleteFailed
from api.router.delete_integration_router import delete_integration


class TestDeleteIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = SimpleNamespace(user_id=uuid4(), organization_id=uuid4())

        self.integration_id = uuid4()
        self.payload = SimpleNamespace(
            integration_id=self.integration_id,
            user_id=uuid4(),
            organization_id=uuid4(),
        )

        self.connector = object()

    @patch('api.router.delete_integration_router.integration_service_cache')
    @patch('api.router.delete_integration_router.get_kafka_message_bus')
    @patch('api.router.delete_integration_router.IntegrationRepository')
    @patch('api.router.delete_integration_router.get_current_identity')
    async def test_success_happy_path(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_get_bus,
        mock_cache,
    ):
        mock_get_current_identity.return_value = self.identity

        repo_instance = Mock()
        repo_instance.delete_integration = AsyncMock(return_value=None)
        mock_repo_cls.return_value = repo_instance

        bus = SimpleNamespace(publish=AsyncMock())
        mock_get_bus.return_value = bus

        mock_cache.delete_by_prefix = AsyncMock()

        result = await delete_integration(self.payload, connector=self.connector)
        self.assertIsNone(result)

        repo_instance.delete_integration.assert_awaited_once_with(
            integration_id=self.payload.integration_id,
            user_id=self.payload.user_id,
            organization_id=self.payload.organization_id,
        )

        call = getattr(bus.publish, 'await_args', None) or bus.publish.call_args
        event = call.args[0]
        self.assertEqual(getattr(event, 'user_id', None), self.identity.user_id)
        self.assertEqual(getattr(event, 'organization_id', None), self.identity.organization_id)
        self.assertEqual(getattr(event, 'integration_id', None), self.integration_id)

        mock_cache.delete_by_prefix.assert_awaited_once_with(
            self.identity.organization_id, self.identity.user_id
        )

    @patch('api.router.delete_integration_router.integration_service_cache')
    @patch('api.router.delete_integration_router.get_kafka_message_bus')
    @patch('api.router.delete_integration_router.IntegrationRepository')
    @patch('api.router.delete_integration_router.get_current_identity')
    async def test_integration_delete_failed_returns_424(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_get_bus,
        mock_cache,
    ):
        mock_get_current_identity.return_value = self.identity


        class DummyDeleteFailed(IntegrationDeleteFailed):
            def __init__(self):
                self._msg = 'not found'
            def __str__(self):
                return self._msg

        repo_instance = Mock()
        repo_instance.delete_integration = AsyncMock(side_effect=DummyDeleteFailed())
        mock_repo_cls.return_value = repo_instance

        mock_get_bus.return_value = SimpleNamespace(publish=AsyncMock())
        mock_cache.delete_by_prefix = AsyncMock()

        with self.assertRaises(HTTPException) as ctx:
            await delete_integration(self.payload, connector=self.connector)

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertEqual(exc.detail, {'message': 'not found'})

        mock_get_bus.return_value.publish.assert_not_awaited()
        mock_cache.delete_by_prefix.assert_not_awaited()

    @patch('api.router.delete_integration_router.integration_service_cache')
    @patch('api.router.delete_integration_router.get_kafka_message_bus')
    @patch('api.router.delete_integration_router.IntegrationRepository')
    @patch('api.router.delete_integration_router.get_current_identity')
    async def test_unexpected_exception_returns_400(
        self,
        mock_get_current_identity,
        mock_repo_cls,
        mock_get_bus,
        mock_cache,
    ):
        mock_get_current_identity.return_value = self.identity

        repo_instance = Mock()
        repo_instance.delete_integration = AsyncMock(side_effect=RuntimeError('boom'))
        mock_repo_cls.return_value = repo_instance

        mock_get_bus.return_value = SimpleNamespace(publish=AsyncMock())
        mock_cache.delete_by_prefix = AsyncMock()

        with self.assertRaises(HTTPException) as ctx:
            await delete_integration(self.payload, connector=self.connector)

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exc.detail, {'message': 'Unexpected error: boom'})

        mock_get_bus.return_value.publish.assert_not_awaited()
        mock_cache.delete_by_prefix.assert_not_awaited()
