import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.session.session_maker import (
    fetch_session_maker,
    session_scope,
)


class TestFetchSessionMaker(unittest.TestCase):
    def setUp(self):
        self.patcher_sessionmaker = patch(
            "nextplore_sdk.database.connection_maker.session.session_maker.sessionmaker"
        )
        self.patcher_scoped_session = patch(
            "nextplore_sdk.database.connection_maker.session.session_maker.scoped_session"
        )

        self.mock_sessionmaker = self.patcher_sessionmaker.start()
        self.mock_scoped_session = self.patcher_scoped_session.start()

        self.addCleanup(self.patcher_sessionmaker.stop)
        self.addCleanup(self.patcher_scoped_session.stop)

    def test_fetch_session_maker_builds_scoped_session_bound_to_engine(self):
        engine = MagicMock(name="Engine")
        session_factory = MagicMock(name="session_factory")
        scoped_factory = MagicMock(name="scoped_session_factory")

        self.mock_sessionmaker.return_value = session_factory
        self.mock_scoped_session.return_value = scoped_factory

        result = fetch_session_maker(engine)

        self.mock_sessionmaker.assert_called_once_with(bind=engine)
        self.mock_scoped_session.assert_called_once_with(session_factory)
        self.assertIs(result, scoped_factory)


class TestSessionScope(unittest.TestCase):
    def test_session_scope_success_commits_and_removes(self):
        session = MagicMock(name="Session")
        scoped_factory = MagicMock(name="scoped_session_factory")
        scoped_factory.return_value = session

        with session_scope(scoped_factory) as s:
            self.assertIs(s, session)

        session.commit.assert_called_once()
        session.rollback.assert_not_called()
        scoped_factory.remove.assert_called_once()

    def test_session_scope_error_rolls_back_removes_and_reraises(self):
        session = MagicMock(name="Session")
        scoped_factory = MagicMock(name="scoped_session_factory")
        scoped_factory.return_value = session

        class Boom(Exception):
            pass

        with self.assertRaises(Boom), session_scope(scoped_factory):
            raise Boom("kaboom")

        session.rollback.assert_called_once()
        session.commit.assert_not_called()
        scoped_factory.remove.assert_called_once()
