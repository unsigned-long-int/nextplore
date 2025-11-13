import unittest
from sqlalchemy.exc import OperationalError
from unittest.mock import MagicMock, patch, call

from nextplore_sdk.database.connection_maker.engine.engine_invoke import invoke_engine
from nextplore_sdk.database.connection_maker.exc.exceptions import ConnectionFailed


class TestInvokeEngine(unittest.TestCase):
    def setUp(self):
        self.engine_mock = MagicMock()
        self.conn_mock = MagicMock()
        self.conn_mock.__enter__.return_value = self.conn_mock
        self.conn_mock.__exit__.return_value = False
        self.engine_mock.connect.return_value = self.conn_mock

    @patch('nextplore_sdk.database.connection_maker.engine.engine_invoke.create_engine')
    def test_invoke_engine_happy_path(self, create_engine_mock):
        creator_mock = MagicMock()
        create_engine_mock.return_value = self.engine_mock

        engine = invoke_engine(
            dialect='dialect',
            creator=creator_mock
        )
        self.assertIs(engine, self.engine_mock)
        create_engine_mock.assert_called_once_with('dialect', creator=creator_mock)
        self.engine_mock.connect.assert_called_once()
        self.conn_mock.execute.assert_called_once()

    @patch('nextplore_sdk.database.connection_maker.engine.engine_invoke.time.sleep')
    @patch('nextplore_sdk.database.connection_maker.engine.engine_invoke.create_engine')
    def test_retries_if_operational_error(self, create_engine_mock, sleep_mock):
        creator_mock = MagicMock()
        create_engine_mock.return_value = self.engine_mock
        create_engine_mock.side_effect = OperationalError('SELECT 1', {}, Exception('db down'))
        with self.assertRaises(ConnectionFailed) as ctx:
            _ = invoke_engine(
                dialect='dialect',
                creator=creator_mock,
                max_retries=3
            )
            self.assertIsInstance(ctx.exception.__cause__, OperationalError)
            create_engine_mock.assert_any_call('dialect', creator=creator_mock)
            self.assertEqual(sleep_mock.call_count, 4)
            self.assertEqual(create_engine_mock.call_count, 3)

    @patch('nextplore_sdk.database.connection_maker.engine.engine_invoke.time.sleep')
    @patch('nextplore_sdk.database.connection_maker.engine.engine_invoke.create_engine')
    def test_retries_if_operational_error_then_succeeds(self, create_engine_mock, sleep_mock):
        create_engine_mock.side_effect = [
            OperationalError('SELECT 1', {}, Exception('db down')),
            OperationalError('SELECT 1', {}, Exception('db down')),
            self.engine_mock,
        ]

        engine = invoke_engine(
            dialect="dialect",
            creator=MagicMock(),
            max_retries=5,
            base_delay=0.5,
            backoff_factor=3,
        )

        self.assertIs(engine, self.engine_mock)
        self.assertEqual(create_engine_mock.call_count, 3)
        sleep_mock.assert_has_calls([call(0.5), call(1.5)])
        self.assertEqual(sleep_mock.call_count, 2)
        self.conn_mock.execute.assert_called_once()


    @patch('nextplore_sdk.database.connection_maker.engine.engine_invoke.time.sleep')
    @patch('nextplore_sdk.database.connection_maker.engine.engine_invoke.create_engine')
    def test_raises_by_general_exception(self, create_engine_mock, sleep_mock):
        create_engine_mock.side_effect = Exception('db down')


        with self.assertRaises(ConnectionFailed) as ctx:
            _ = invoke_engine(
                dialect="dialect",
                creator=MagicMock(),
                max_retries=5,
                base_delay=0.5,
                backoff_factor=3,
            )
            sleep_mock.assert_not_called()
            self.assertIn('Unexpected connection failure.', str(ctx.exception))
