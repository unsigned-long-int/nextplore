import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.driver_adapters.mysql.pymysql_adapter import \
    MysqlPyMysqlAdapter


class TestMysqlPyMysqlAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = MysqlPyMysqlAdapter()

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.mysql.pymysql_adapter.ssl')
    @patch('nextplore_sdk.database.connection_maker.driver_adapters.mysql.pymysql_adapter.pymysql')
    def test_connect_happy_path(
        self,
        pymysql_mock,
        ssl_mock
    ):
        ctx = MagicMock()
        ssl_mock.create_default_context.return_value = ctx
        self.adapter.connect(
            host='localhost',
            database='mydb',
            port=3306,
            username='root',
            password='password',
            ca_path='/test.ca',
            timeout=20
        )
        ssl_mock.create_default_context.assert_called_once_with(cafile='/test.ca')
        pymysql_mock.connect.assert_called_once_with(
            host='localhost',
            port=3306,
            db='mydb',
            user='root',
            password='password',
            ssl=ctx,
            connect_timeout=20
        )

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.mysql.pymysql_adapter.ssl')
    @patch('nextplore_sdk.database.connection_maker.driver_adapters.mysql.pymysql_adapter.pymysql')
    def test_connect_forwards_defaults(
        self,
        pymysql_mock,
        ssl_mock
    ):
        ctx = MagicMock()
        ssl_mock.create_default_context.return_value = ctx
        self.adapter.connect(
            host='localhost',
            database='mydb',
        )
        ssl_mock.create_default_context.assert_called_once_with()
        pymysql_mock.connect.assert_called_once_with(
            host='localhost',
            port=None,
            db='mydb',
            user=None,
            password=None,
            ssl=ctx,
            connect_timeout=10
        )
