import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status

from api.router.update_integration_router import update_integration


class TestUpdateIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = SimpleNamespace(user_id=uuid4(), organization_id=uuid4())
        self.payload = SimpleNamespace(
            integration_id=uuid4(),
            user_id=uuid4(),
            organization_id=uuid4(),
            update_args={'connection_name': 'new-name', 'autosync_on': True},
        )
        self.connector = object()

    @patch('api.router.update_integration_router.integration_service_cache')
    @patch('api.router.update_integration_router.IntegrationRepository')
    @patch('api.router.update_integration_router.get_current_identity')
    async def test_success_happy_path(self, mock_get_current_identity, mock_repo_cls, mock_cache):
        mock_get_current_identity.return_value = self.identity

        repo = Mock()
        repo.update_integration = AsyncMock(return_value=None)
        mock_repo_cls.return_value = repo

        mock_cache.delete_by_prefix = AsyncMock()

        result = await update_integration(self.payload, connector=self.connector)
        self.assertIsNone(result)

        mock_repo_cls.assert_called_once_with(self.connector)
        repo.update_integration.assert_awaited_once_with(
            integration_id=self.payload.integration_id,
            user_id=self.payload.user_id,
            organization_id=self.payload.organization_id,
            update_args=self.payload.update_args,
        )
        mock_cache.delete_by_prefix.assert_awaited_once_with(
            self.identity.organization_id, self.identity.user_id
        )

    @patch('api.router.update_integration_router.integration_service_cache')
    @patch('api.router.update_integration_router.IntegrationRepository')
    @patch('api.router.update_integration_router.get_current_identity')
    async def test_integration_update_failed_raises_404(self, mock_get_current_identity, mock_repo_cls, mock_cache):
        mock_get_current_identity.return_value = self.identity

        from database.repositories import IntegrationUpdateFailed

        class DummyUpdateFailed(IntegrationUpdateFailed):
            def __init__(self):
                self._msg = 'not found'
            def __str__(self):
                return self._msg

        repo = Mock()
        repo.update_integration = AsyncMock(side_effect=DummyUpdateFailed())
        mock_repo_cls.return_value = repo

        mock_cache.delete_by_prefix = AsyncMock()

        with self.assertRaises(HTTPException) as ctx:
            await update_integration(self.payload, connector=self.connector)

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc.detail, 'not found')
        mock_cache.delete_by_prefix.assert_not_awaited()

    @patch('api.router.update_integration_router.integration_service_cache')
    @patch('api.router.update_integration_router.IntegrationRepository')
    @patch('api.router.update_integration_router.get_current_identity')
    async def test_sqlalchemy_error_raises_500(self, mock_get_current_identity, mock_repo_cls, mock_cache):
        mock_get_current_identity.return_value = self.identity

        from sqlalchemy.exc import SQLAlchemyError

        repo = Mock()
        repo.update_integration = AsyncMock(side_effect=SQLAlchemyError('db down'))
        mock_repo_cls.return_value = repo

        mock_cache.delete_by_prefix = AsyncMock()

        with self.assertRaises(HTTPException) as ctx:
            await update_integration(self.payload, connector=self.connector)

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(exc.detail, 'Database error: db down')
        mock_cache.delete_by_prefix.assert_not_awaited()

    @patch('api.router.update_integration_router.integration_service_cache')
    @patch('api.router.update_integration_router.IntegrationRepository')
    @patch('api.router.update_integration_router.get_current_identity')
    async def test_unhandled_error_raises_400(self, mock_get_current_identity, mock_repo_cls, mock_cache):
        mock_get_current_identity.return_value = self.identity

        repo = Mock()
        repo.update_integration = AsyncMock(side_effect=RuntimeError('boom'))
        mock_repo_cls.return_value = repo

        mock_cache.delete_by_prefix = AsyncMock()

        with self.assertRaises(HTTPException) as ctx:
            await update_integration(self.payload, connector=self.connector)

        exc = ctx.exception
        self.assertEqual(exc.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exc.detail, 'Unhandled error: boom')
        mock_cache.delete_by_prefix.assert_not_awaited()
