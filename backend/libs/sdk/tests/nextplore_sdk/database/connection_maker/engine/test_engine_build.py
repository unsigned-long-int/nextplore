import unittest
from unittest.mock import MagicMock, patch, AsyncMock

from nextplore_sdk.database.connection_maker.engine.engine_build import build_engine, invoke_engine
from nextplore_sdk.database.connection_maker.exc.exceptions import MissingRegistry


class TestBuildEngine(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.profile_mock = MagicMock()
        self.profile_mock.cloud = 'cloud'
        self.profile_mock.db = 'db'
        self.profile_mock.auth = 'auth'

        self.strategy_mock = MagicMock()
        self.adapter_mock = MagicMock()
        self.creds_provider_mock = MagicMock()

        self.adapter_mock.DIALECT = 'postgresql+psycopg'

        self.strategy_instance = self.strategy_mock.return_value
        self.strategy_instance.pool_settings.return_value = {'pool_size': 5}

        self.adapter_instance = self.adapter_mock.return_value
        self.creds_instance = self.creds_provider_mock.return_value

    @patch('nextplore_sdk.database.connection_maker.engine.engine_build.asyncio.to_thread', new_callable=AsyncMock)
    @patch('nextplore_sdk.database.connection_maker.engine.engine_build.STRATEGY_REGISTRY')
    async def test_build_happy_path(self, strategy_registry_mock, to_thread_mock):
        engine_mock = MagicMock()
        to_thread_mock.return_value = engine_mock

        strategies = {
            ('cloud', 'db', 'auth'): (
                self.strategy_mock,
                self.adapter_mock,
                self.creds_provider_mock
            )
        }
        strategy_registry_mock.__getitem__.side_effect = lambda k: strategies[k]

        engine = await build_engine(self.profile_mock)

        self.assertIs(engine, engine_mock)
        self.strategy_mock.assert_called_once_with(self.profile_mock)
        self.adapter_mock.assert_called_once_with()
        self.creds_provider_mock.assert_called_once_with(self.profile_mock)
        self.strategy_instance.make_creator.assert_called_once_with(
            adapter=self.adapter_instance,
            creds_provider=self.creds_instance
        )

        self.strategy_instance.pool_settings.assert_called_once_with()

        to_thread_mock.assert_awaited_once_with(
            invoke_engine,
            self.adapter_mock.DIALECT,
            creator=self.strategy_instance.make_creator.return_value,
            **self.strategy_instance.pool_settings.return_value
        )

    @patch('nextplore_sdk.database.connection_maker.engine.engine_build.asyncio.to_thread', new_callable=AsyncMock)
    @patch('nextplore_sdk.database.connection_maker.engine.engine_build.STRATEGY_REGISTRY')
    async def test_build_raises_if_missing_strategy(self, strategy_registry_mock, to_thread_mock):
        engine_mock = MagicMock()
        to_thread_mock.return_value = engine_mock

        strategies = {
            ('cloud', 'db', 'something else'): (
                self.strategy_mock,
                self.adapter_mock,
                self.creds_provider_mock
            )
        }
        strategy_registry_mock.__getitem__.side_effect = lambda k: strategies[k]
        with self.assertRaises(MissingRegistry) as ctx:
            _ = await build_engine(self.profile_mock)
            self.assertIs(ctx.exception, MissingRegistry)
            self.assertIn('Strategy is not found in registry', str(ctx.exception))
            to_thread_mock.assert_not_awaited()

    @patch('nextplore_sdk.database.connection_maker.engine.engine_build.asyncio.to_thread', new_callable=AsyncMock)
    @patch('nextplore_sdk.database.connection_maker.engine.engine_build.STRATEGY_REGISTRY')
    async def test_build_not_sets_creds_provider_kwargs(self, strategy_registry_mock, to_thread_mock):
        engine_mock = MagicMock()
        to_thread_mock.return_value = engine_mock

        strategies = {
            ('cloud', 'db', 'auth'): (
                self.strategy_mock,
                self.adapter_mock,
                None
            )
        }
        strategy_registry_mock.__getitem__.side_effect = lambda k: strategies[k]
        _ = await build_engine(self.profile_mock)
        self.strategy_mock.assert_called_once_with(self.profile_mock)
        self.strategy_instance.make_creator.assert_called_once_with(
            adapter=self.adapter_instance
        )
