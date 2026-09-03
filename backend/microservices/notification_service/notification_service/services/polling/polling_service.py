import asyncio
import logging
from datetime import datetime, timedelta, timezone

from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from sqlalchemy import text

from notification_service.services.notification import (
    NotificationFailed,
    NotificationService,
)

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 15
BATCH_SIZE = 20
MAX_ATTEMPTS = 5
BACKOFF_MINUTES = [1, 5, 15, 60, 240]


class EmailOutboxPoller:
    def __init__(
        self,
        db_connector: DatabaseBackendConnector,
        notification_service: NotificationService,
    ) -> None:
        self._db = db_connector
        self._notification = notification_service
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("Email outbox poller started")
        while self._running:
            try:
                await self._poll()
            except Exception as e:
                logger.error(
                    f"Unexpected error in email poller cycle - continuing: {e!s}",
                    exc_info=True,
                )
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    def stop(self) -> None:
        self._running = False
        logger.info("Email outbox poller stopped")

    async def _poll(self) -> None:
        async with self._db.session_scope() as session:
            rows = (
                await session.execute(
                    text("""
                    SELECT id, recipient, subject, html, attempts
                    FROM notification.email_outbox
                    WHERE status = 'pending'
                      AND next_attempt_at <= NOW()
                      AND attempts < :max_attempts
                    ORDER BY next_attempt_at
                    LIMIT :batch_size
                    FOR UPDATE SKIP LOCKED
                """),
                    {"max_attempts": MAX_ATTEMPTS, "batch_size": BATCH_SIZE},
                )
            ).fetchall()

        if not rows:
            return

        logger.info(f"Picked up {len(rows)} outbox rows")

        for row in rows:
            await self._dispatch(row)

    async def _dispatch(self, row) -> None:
        now = datetime.now(timezone.utc)
        attempt = row.attempts + 1

        try:
            await self._notification.send_email(row.recipient, row.subject, row.html)

            async with self._db.session_scope() as session:
                await session.execute(
                    text("""
                        UPDATE notification.email_outbox
                        SET status = 'sent',
                            sent_at = :now,
                            attempts = :attempt
                        WHERE id = :id
                    """),
                    {"now": now, "attempt": attempt, "id": row.id},
                )
            logger.info(f"Sent email outbox row {row.id} to {row.recipient}")

        except NotificationFailed as e:
            backoff = BACKOFF_MINUTES[min(attempt - 1, len(BACKOFF_MINUTES) - 1)]
            next_attempt = now + timedelta(minutes=backoff)
            new_status = "failed" if attempt >= MAX_ATTEMPTS else "pending"

            async with self._db.session_scope() as session:
                await session.execute(
                    text("""
                        UPDATE notification.email_outbox
                        SET status = :status,
                            attempts = :attempt,
                            next_attempt_at = :next_attempt,
                            last_error = :error
                        WHERE id = :id
                    """),
                    {
                        "status": new_status,
                        "attempt": attempt,
                        "next_attempt": next_attempt,
                        "error": str(e),
                        "id": row.id,
                    },
                )
            logger.warning(
                f"Outbox row {row.id} attempt {attempt}/{MAX_ATTEMPTS} failed - "
                f"{'permanently failed' if new_status == 'failed' else f'retry in {backoff}m'}"
            )
