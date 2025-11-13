import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_adapter import SnowflakeAdapter


class TestSnowflakeAdapter(unittest.TestCase):
    def setUp(self):
        self.conn_mock = MagicMock()
        self.snowflake_adapter = SnowflakeAdapter()

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_adapter.snowflake.connector')
    def test_connect_happy_path(self, snowflake_mock):
        snowflake_mock.connect.return_value = self.conn_mock
        conn = self.snowflake_adapter.connect(
            host='localhost',
            database='mydb',
            username='user',
            password='password',
            warehouse='mywarehouse',
            timeout=20
        )
        self.assertIs(conn, self.conn_mock)
        snowflake_mock.connect.assert_called_once_with(
            account='localhost',
            user='user',
            password='password',
            warehouse='mywarehouse',
            database='mydb',
            timeout=20
        )

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_adapter.snowflake.connector')
    def test_connect_forwards_default(self, snowflake_mock):
        snowflake_mock.connect.return_value = self.conn_mock
        conn = self.snowflake_adapter.connect(
            host='localhost',
            database='mydb',
            warehouse='mywarehouse'
        )
        self.assertIs(conn, self.conn_mock)
        snowflake_mock.connect.assert_called_once_with(
            account='localhost',
            user=None,
            password=None,
            warehouse='mywarehouse',
            database='mydb',
            timeout=10
        )

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_adapter.snowflake.connector')
    def test_raises_if_no_warehouse(self, snowflake_mock):
        snowflake_mock.connect.return_value = self.conn_mock
        with self.assertRaises(AttributeError):
            self.snowflake_adapter.connect(
                host='localhost',
                database='mydb',
            )
        snowflake_mock.connect.assert_not_called()
