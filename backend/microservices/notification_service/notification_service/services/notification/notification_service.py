import os
import logging
from azure.communication.email.aio import EmailClient


logger = logging.getLogger(__name__)


class NotificationFailed(Exception):
    pass


class NotificationService:
    def __init__(self) -> None:
        conn_str = os.getenv('AZURE_COMMUNICATION_CONNECTION_STRING', '')
        if not conn_str:
            raise RuntimeError('AZURE_COMMUNICATION_CONNECTION_STRING environment variable not set')

        self._client = EmailClient.from_connection_string(conn_str)
        self._from = os.getenv('NEXTPLORE_FROM_EMAIL', 'DoNotReply@nextplore.co')
        self._admin = os.getenv('NEXTPLORE_ADMIN_EMAIL', 'admin@nextplore.co')
        self._app_url = os.getenv('NEXTPLORE_APP_URL', 'http://localhost:5173')

    async def _send(self, to: str, subject: str, html: str) -> None:
        try:
            poller = await self._client.begin_send({
                'senderAddress': self._from,
                'recipients': {'to': [{'address': to}]},
                'content': {'subject': subject, 'html': html},
            })
            await poller.result()
        except Exception as e:
            msg = f'Failed to send notification due to Azure client communication error: {str(e)}'
            logger.error(
                msg,
                extra={'from': self._from, 'to': to},
                exc_info=True,
            )
            raise NotificationFailed(msg) from e

    async def send_email(self, to: str, subject: str, html: str) -> None:
        await self._send(to=to, subject=subject, html=html)

    async def close(self) -> None:
        await self._client.close()
