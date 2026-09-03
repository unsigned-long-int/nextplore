import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession

from nextplore_orchestrator.database.exceptions import EmailOutboxCreateFailed
from nextplore_orchestrator.database.models import EmailOutboxORM

logger = logging.getLogger(__name__)


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_email_outbox(
        self,
        recipient: str,
        subject: str,
        html: str,
    ) -> UUID:
        try:
            mail_outbox_orm = EmailOutboxORM(
                recipient=recipient, subject=subject, html=html
            )
            self._session.add(mail_outbox_orm)
            await self._session.flush()
            return mail_outbox_orm.id
        except SQLAlchemyError as e:
            msg = f"Create mail outbox failed with database error: {e!s}"
            logger.exception(msg)
            raise EmailOutboxCreateFailed(msg) from e
