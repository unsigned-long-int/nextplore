from contextlib import asynccontextmanager
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

from notification_service.services.polling.polling_service import EmailOutboxPoller, BACKOFF_MINUTES, MAX_ATTEMPTS
from notification_service.services.notification import NotificationFailed


def _make_row(id='row-1', recipient='user@example.com', subject='Subject', html='<p>Hi</p>', attempts=0):
    row = MagicMock()
    row.id = id
    row.recipient = recipient
    row.subject = subject
    row.html = html
    row.attempts = attempts
    return row


def _make_session():
    session = AsyncMock()

    @asynccontextmanager
    async def _begin():
        yield

    session.begin = _begin
    return session


def _make_db_connector(sessions: list):
    db_connector = MagicMock()
    session_iter = iter(sessions)

    @asynccontextmanager
    async def _session_scope():
        yield next(session_iter)

    db_connector.session_scope = _session_scope
    return db_connector


def _make_poller(poll_session=None, dispatch_sessions=None):
    if poll_session is None:
        poll_session = _make_session()
    if dispatch_sessions is None:
        dispatch_sessions = []
    db_connector = _make_db_connector([poll_session] + dispatch_sessions)
    notification_svc = AsyncMock()
    poller = EmailOutboxPoller(db_connector=db_connector, notification_service=notification_svc)
    return poller, notification_svc, poll_session


def _make_dispatch_poller(dispatch_sessions=None):
    if dispatch_sessions is None:
        dispatch_sessions = [_make_session()]
    db_connector = _make_db_connector(dispatch_sessions)
    notification_svc = AsyncMock()
    poller = EmailOutboxPoller(db_connector=db_connector, notification_service=notification_svc)
    return poller, notification_svc, dispatch_sessions[0]


class TestEmailOutboxPollerStop(unittest.IsolatedAsyncioTestCase):

    def test_stop_sets_running_false(self):
        poller, _, _ = _make_poller()
        poller._running = True
        poller.stop()
        self.assertFalse(poller._running)


class TestEmailOutboxPollerPoll(unittest.IsolatedAsyncioTestCase):

    async def test_poll_dispatches_each_row(self):
        poll_session = _make_session()
        rows = [_make_row(id='row-1'), _make_row(id='row-2')]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = rows
        poll_session.execute = AsyncMock(return_value=mock_result)

        dispatch_sessions = [_make_session(), _make_session()]
        poller, _, _ = _make_poller(poll_session=poll_session, dispatch_sessions=dispatch_sessions)

        with patch.object(poller, '_dispatch', new_callable=AsyncMock) as mock_dispatch:
            await poller._poll()
            self.assertEqual(mock_dispatch.await_count, 2)
            dispatched_rows = [c.args[0] for c in mock_dispatch.await_args_list]
            self.assertIn(rows[0], dispatched_rows)
            self.assertIn(rows[1], dispatched_rows)

    async def test_poll_does_nothing_when_no_rows(self):
        poll_session = _make_session()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        poll_session.execute = AsyncMock(return_value=mock_result)

        poller, _, _ = _make_poller(poll_session=poll_session)

        with patch.object(poller, '_dispatch', new_callable=AsyncMock) as mock_dispatch:
            await poller._poll()
            mock_dispatch.assert_not_awaited()


class TestEmailOutboxPollerDispatch(unittest.IsolatedAsyncioTestCase):

    async def test_dispatch_success_marks_sent(self):
        poller, notification_svc, dispatch_session = _make_dispatch_poller()
        dispatch_session.execute = AsyncMock()
        row = _make_row(attempts=0)

        await poller._dispatch(row)

        notification_svc.send_email.assert_awaited_once_with(row.recipient, row.subject, row.html)
        sql, params = dispatch_session.execute.await_args.args
        self.assertIn('sent', sql.text)
        self.assertEqual(params['attempt'], 1)
        self.assertEqual(params['id'], row.id)
        self.assertIn('now', params)

    async def test_dispatch_failure_marks_pending_with_backoff(self):
        poller, notification_svc, dispatch_session = _make_dispatch_poller()
        dispatch_session.execute = AsyncMock()
        notification_svc.send_email.side_effect = NotificationFailed('timeout')
        row = _make_row(attempts=0)

        await poller._dispatch(row)

        params = dispatch_session.execute.await_args.args[1]
        self.assertEqual(params['status'], 'pending')
        self.assertEqual(params['attempt'], 1)
        self.assertIn('timeout', params['error'])

    async def test_dispatch_marks_failed_on_max_attempts(self):
        poller, notification_svc, dispatch_session = _make_dispatch_poller()
        dispatch_session.execute = AsyncMock()
        notification_svc.send_email.side_effect = NotificationFailed('timeout')
        row = _make_row(attempts=MAX_ATTEMPTS - 1)

        await poller._dispatch(row)

        params = dispatch_session.execute.await_args.args[1]
        self.assertEqual(params['status'], 'failed')
        self.assertEqual(params['attempt'], MAX_ATTEMPTS)

    async def test_dispatch_backoff_increases_with_attempts(self):
        fixed_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        for attempt_index, expected_backoff in enumerate(BACKOFF_MINUTES):
            dispatch_session = _make_session()
            dispatch_session.execute = AsyncMock()
            poller, notification_svc, _ = _make_dispatch_poller(dispatch_sessions=[dispatch_session])
            notification_svc.send_email.side_effect = NotificationFailed('err')
            row = _make_row(attempts=attempt_index)

            with patch('notification_service.services.polling.polling_service.datetime') as mock_dt:
                mock_dt.now.return_value = fixed_now
                mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

                await poller._dispatch(row)
                params = dispatch_session.execute.await_args.args[1]
                expected_next = fixed_now + timedelta(minutes=expected_backoff)
                self.assertEqual(params['next_attempt'], expected_next)
