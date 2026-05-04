import unittest
from unittest.mock import AsyncMock, patch
import os

from notification_service.services.notification import NotificationService, NotificationFailed


CONN_STR = 'endpoint=https://test.communication.azure.com/;accesskey=dGVzdA=='


class TestNotificationService(unittest.IsolatedAsyncioTestCase):

    def _make_service(self) -> NotificationService:
        with patch('notification_service.services.notification.notification_service.EmailClient') as mock_client_cls:
            mock_client_cls.from_connection_string.return_value = AsyncMock()
            svc = NotificationService()
        return svc


    def test_init_raises_if_conn_str_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('AZURE_COMMUNICATION_CONNECTION_STRING', None)
            with self.assertRaises(RuntimeError):
                NotificationService()

    def test_init_succeeds_with_conn_str(self):
        with patch.dict(os.environ, {'AZURE_COMMUNICATION_CONNECTION_STRING': CONN_STR}):
            with patch('notification_service.services.notification.notification_service.EmailClient'):
                svc = NotificationService()
                self.assertIsNotNone(svc)


    async def test_send_email_calls_begin_send_with_correct_payload(self):
        with patch.dict(os.environ, {
            'AZURE_COMMUNICATION_CONNECTION_STRING': CONN_STR,
            'NEXTPLORE_FROM_EMAIL': 'no-reply@nextplore.co',
        }):
            with patch('notification_service.services.notification.notification_service.EmailClient') as mock_cls:
                mock_poller = AsyncMock()
                mock_client = AsyncMock()
                mock_client.begin_send.return_value = mock_poller
                mock_cls.from_connection_string.return_value = mock_client

                svc = NotificationService()
                await svc.send_email('user@example.com', 'Subject', '<p>Hello</p>')

                mock_client.begin_send.assert_called_once_with({
                    'senderAddress': 'no-reply@nextplore.co',
                    'recipients': {'to': [{'address': 'user@example.com'}]},
                    'content': {'subject': 'Subject', 'html': '<p>Hello</p>'},
                })
                mock_poller.result.assert_awaited_once()

    async def test_send_email_raises_notification_failed_on_azure_error(self):
        with patch.dict(os.environ, {'AZURE_COMMUNICATION_CONNECTION_STRING': CONN_STR}):
            with patch('notification_service.services.notification.notification_service.EmailClient') as mock_cls:
                mock_client = AsyncMock()
                mock_client.begin_send.side_effect = Exception('Azure timeout')
                mock_cls.from_connection_string.return_value = mock_client

                svc = NotificationService()
                with self.assertRaises(NotificationFailed):
                    await svc.send_email('user@example.com', 'Subject', '<p>Hello</p>')

    async def test_send_email_raises_notification_failed_on_poller_error(self):
        with patch.dict(os.environ, {'AZURE_COMMUNICATION_CONNECTION_STRING': CONN_STR}):
            with patch('notification_service.services.notification.notification_service.EmailClient') as mock_cls:
                mock_poller = AsyncMock()
                mock_poller.result.side_effect = Exception('Poller failed')
                mock_client = AsyncMock()
                mock_client.begin_send.return_value = mock_poller
                mock_cls.from_connection_string.return_value = mock_client

                svc = NotificationService()
                with self.assertRaises(NotificationFailed):
                    await svc.send_email('user@example.com', 'Subject', '<p>Hello</p>')

    async def test_notification_failed_wraps_original_exception(self):
        with patch.dict(os.environ, {'AZURE_COMMUNICATION_CONNECTION_STRING': CONN_STR}):
            with patch('notification_service.services.notification.notification_service.EmailClient') as mock_cls:
                original = Exception('root cause')
                mock_client = AsyncMock()
                mock_client.begin_send.side_effect = original
                mock_cls.from_connection_string.return_value = mock_client

                svc = NotificationService()
                with self.assertRaises(NotificationFailed) as ctx:
                    await svc.send_email('user@example.com', 'Subject', '<p>Hi</p>')

                self.assertIs(ctx.exception.__cause__, original)


    async def test_close_calls_client_close(self):
        with patch.dict(os.environ, {'AZURE_COMMUNICATION_CONNECTION_STRING': CONN_STR}):
            with patch('notification_service.services.notification.notification_service.EmailClient') as mock_cls:
                mock_client = AsyncMock()
                mock_cls.from_connection_string.return_value = mock_client

                svc = NotificationService()
                await svc.close()

                mock_client.close.assert_awaited_once()

