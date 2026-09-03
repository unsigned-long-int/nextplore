import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from sqlalchemy.ext.asyncio import AsyncSession


class TestDatabaseBackendConnector(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.database_backend_connector = DatabaseBackendConnector()

    @patch(
        "nextplore_sdk.database.backend.database_backend_connector.create_async_engine"
    )
    @patch(
        "nextplore_sdk.database.backend.database_backend_connector.async_sessionmaker"
    )
    def test_init_idempotent(self, async_sessionmaker_mock, create_async_engine_mock):
        self.database_backend_connector.init()
        engine1 = self.database_backend_connector._engine
        session1 = self.database_backend_connector._sessionmaker
        self.database_backend_connector.init()
        create_async_engine_mock.assert_called_once_with(
            self.database_backend_connector._url,
            echo=False,
            future=True,
            pool_size=5,
            max_overflow=5,
            pool_timeout=5,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
        async_sessionmaker_mock.assert_called_once_with(
            bind=self.database_backend_connector._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self.assertIs(engine1, self.database_backend_connector._engine)
        self.assertIs(session1, self.database_backend_connector._sessionmaker)

    @patch(
        "nextplore_sdk.database.backend.database_backend_connector.create_async_engine"
    )
    @patch(
        "nextplore_sdk.database.backend.database_backend_connector.async_sessionmaker"
    )
    async def test_scoped_with_rls(
        self, async_sessionmaker_mock, create_async_engine_mock
    ):
        self.database_backend_connector._sessionmaker = None
        self.database_backend_connector._engine = None

        session_factory_mock = AsyncMock(spec=AsyncSession)
        cm_mock = AsyncMock()
        cm_mock.__aenter__.return_value = session_factory_mock
        cm_mock.__aexit__.return_value = False

        session_maker_callable = MagicMock()
        session_maker_callable.return_value = cm_mock

        async_sessionmaker_mock.return_value = session_maker_callable
        org = uuid.uuid4()
        usr = uuid.uuid4()
        async with self.database_backend_connector.session_scope(
            org, usr
        ) as session_scope:
            self.assertIs(session_scope, session_factory_mock)
            executed_sql = [
                str(call.args[0])
                for call in session_factory_mock.execute.call_args_list
            ]
            self.assertIn("set_config('app.organization_id'", executed_sql[0].lower())
            self.assertIn("set_config('app.user_id'", executed_sql[1].lower())
            self.assertIn("set local statement_timeout", executed_sql[2].lower())
            self.assertIn("set local lock_timeout", executed_sql[3].lower())

    @patch(
        "nextplore_sdk.database.backend.database_backend_connector.create_async_engine"
    )
    @patch(
        "nextplore_sdk.database.backend.database_backend_connector.async_sessionmaker"
    )
    async def test_session_rolls_back_if_exception_raised(
        self, async_sessionmaker_mock, create_async_engine_mock
    ):
        self.database_backend_connector._sessionmaker = None
        self.database_backend_connector._engine = None

        session_factory_mock = AsyncMock(spec=AsyncSession)
        session_factory_mock.execute.side_effect = RuntimeError("Boom")

        cm_mock = AsyncMock()
        cm_mock.__aenter__.return_value = session_factory_mock
        cm_mock.__aexit__.return_value = False

        session_maker_callable = MagicMock()
        session_maker_callable.return_value = cm_mock

        async_sessionmaker_mock.return_value = session_maker_callable
        org = uuid.uuid4()
        usr = uuid.uuid4()
        with self.assertRaises(RuntimeError):
            async with self.database_backend_connector.session_scope(org, usr):
                pass

        session_factory_mock.rollback.assert_awaited()
        session_factory_mock.commit.assert_not_awaited()
