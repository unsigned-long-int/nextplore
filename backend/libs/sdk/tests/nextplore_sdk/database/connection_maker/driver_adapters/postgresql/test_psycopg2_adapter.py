import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.driver_adapters.postgresql.psycopg2_adapter import \
    PostgresqlPsycopg2Adapter


class TestPostgresqlPsycopg2Adapter(unittest.TestCase):
    def setUp(self):
        self.adapter = PostgresqlPsycopg2Adapter()

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.postgresql.psycopg2_adapter.psycopg2')
    def test_connect_happy_path(self, psycopg2_mock):
        conn_mock = MagicMock()
        psycopg2_mock.connect.return_value = conn_mock
        conn = self.adapter.connect(
            host='localhost',
            database='mydb',
            port=5432,
            username='user',
            password='password',
            ca_path='/path/to/ca.crt',
            timeout=20
        )
        self.assertIs(conn, conn_mock)
        psycopg2_mock.connect.assert_called_once_with(
            host='localhost',
            port=5432,
            dbname='mydb',
            user='user',
            password='password',
            sslmode='verify-full',
            sslrootcert='/path/to/ca.crt',
            connect_timeout=20
        )

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.postgresql.psycopg2_adapter.psycopg2')
    def test_connect_forwards_default(self, psycopg2_mock):
        conn_mock = MagicMock()
        psycopg2_mock.connect.return_value = conn_mock
        conn = self.adapter.connect(
            host='localhost',
            database='mydb'
        )
        self.assertIs(conn, conn_mock)
        psycopg2_mock.connect.assert_called_once_with(
            host='localhost',
            port=None,
            dbname='mydb',
            user=None,
            password=None,
            sslmode='verify-full',
            sslrootcert=None,
            connect_timeout=10
        )
