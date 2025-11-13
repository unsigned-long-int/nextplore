import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.driver_adapters.sqlserver.pyodbc_adapter import SqlserverPyOdbcAdapter


class TestSqlserverPyOdbcAdapter(unittest.TestCase):
    def setUp(self):
        self.conn_mock = MagicMock()
        self.adapter = SqlserverPyOdbcAdapter()

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.sqlserver.pyodbc_adapter.pyodbc')
    def test_connect_happy_path_without_attrs(self, pyodbc_mock):
        pyodbc_mock.connect.return_value = self.conn_mock
        conn = self.adapter.connect(
            host='localhost',
            database='mydb',
            port=1433,
            username='myuser',
            password='password',
            timeout=20,
            attrs_before=None
        )
        self.assertIs(conn, self.conn_mock)
        expected_args = (
            'Driver={ODBC Driver 18 for SQL Server};'
            'Server=tcp:localhost,1433;'
            'UID=myuser;'
            'PWD=password;'
            'Database=mydb;'
            'Encrypt=Yes;'
            'TrustServerCertificate=No;'
            'LoginTimeout=20;'
        )
        pyodbc_mock.connect.assert_called_once_with(
            expected_args
        )

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.sqlserver.pyodbc_adapter.pyodbc')
    def test_connect_happy_path_with_attrs(self, pyodbc_mock):
        pyodbc_mock.connect.return_value = self.conn_mock
        conn = self.adapter.connect(
            host='localhost',
            database='mydb',
            port=1433,
            username='myuser',
            password='password',
            timeout=20,
            attrs_before={'test_key': 'test_value'}
        )
        self.assertIs(conn, self.conn_mock)
        expected_args = (
            'Driver={ODBC Driver 18 for SQL Server};'
            'Server=tcp:localhost,1433;'
            'Database=mydb;'
            'Encrypt=Yes;'
            'TrustServerCertificate=No;'
            'LoginTimeout=20;'
        )
        pyodbc_mock.connect.assert_called_once_with(
            expected_args,
            attrs_before={'test_key': 'test_value'}
        )