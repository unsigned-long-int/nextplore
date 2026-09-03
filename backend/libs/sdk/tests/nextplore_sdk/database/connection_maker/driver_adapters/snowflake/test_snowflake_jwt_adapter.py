import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_jwt_adapter import (
    SnowflakeJwtAdapter,
)


class TestSnowflakeAdapter(unittest.TestCase):
    def setUp(self):
        self.conn_mock = MagicMock()
        self.snowflake_adapter = SnowflakeJwtAdapter()

    @patch(
        "nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_jwt_adapter.snowflake.connector"
    )
    def test_connect_happy_path(self, snowflake_mock):
        snowflake_mock.connect.return_value = self.conn_mock
        conn = self.snowflake_adapter.connect(
            host="localhost",
            database="mydb",
            username="user",
            warehouse="mywarehouse",
            private_key="myprivatekey",
            timeout=20,
        )
        self.assertIs(conn, self.conn_mock)
        snowflake_mock.connect.assert_called_once_with(
            account="localhost",
            user="user",
            authenticator="SNOWFLAKE_JWT",
            private_key="myprivatekey",
            warehouse="mywarehouse",
            database="mydb",
            timeout=20,
        )

    @patch(
        "nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_jwt_adapter.snowflake.connector"
    )
    def test_connect_forwards_default(self, snowflake_mock):
        snowflake_mock.connect.return_value = self.conn_mock
        conn = self.snowflake_adapter.connect(
            host="localhost",
            database="mydb",
            warehouse="mywarehouse",
            private_key="myprivatekey",
        )
        self.assertIs(conn, self.conn_mock)
        snowflake_mock.connect.assert_called_once_with(
            account="localhost",
            user=None,
            authenticator="SNOWFLAKE_JWT",
            warehouse="mywarehouse",
            private_key="myprivatekey",
            database="mydb",
            timeout=10,
        )

    @patch(
        "nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_jwt_adapter.snowflake.connector"
    )
    def test_raises_if_no_warehouse(self, snowflake_mock):
        snowflake_mock.connect.return_value = self.conn_mock
        with self.assertRaises(AttributeError) as ctx:
            self.snowflake_adapter.connect(
                host="localhost",
                database="mydb",
                private_key="myprivatekey",
            )

        self.assertIn("private_key and warehouse must be provided", str(ctx.exception))
        snowflake_mock.connect.assert_not_called()

    @patch(
        "nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_jwt_adapter.snowflake.connector"
    )
    def test_raises_if_no_private_key(self, snowflake_mock):
        snowflake_mock.connect.return_value = self.conn_mock
        with self.assertRaises(AttributeError) as ctx:
            self.snowflake_adapter.connect(
                host="localhost",
                database="mydb",
                warehouse="mywarehouse",
            )

        self.assertIn("private_key and warehouse must be provided", str(ctx.exception))
        snowflake_mock.connect.assert_not_called()
