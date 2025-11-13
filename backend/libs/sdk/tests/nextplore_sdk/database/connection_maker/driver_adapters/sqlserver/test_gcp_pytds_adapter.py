import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.driver_adapters.sqlserver.gcp_pytds_adapter \
    import GcpSqlserverPyTdsAdapter, IPTypes


class TestGcpSqlserverPyTdsAdapter(unittest.TestCase):
    def setUp(self):
        self.conn_mock = MagicMock()
        self.connector_mock = MagicMock()
        self.connector_mock.connect.return_value = self.conn_mock
        self.creds_path = '/Users/nik/Downloads/nextplore-470323-18ec66288496.json'
        self.adapter = GcpSqlserverPyTdsAdapter()

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.sqlserver.gcp_pytds_adapter.GcpCloudSqlConnector')
    def test_connect_happy_path(self, gcp_cloud_sql_connector_mock):
        gcp_cloud_sql_connector_mock.get.return_value = self.connector_mock
        conn = self.adapter.connect(
            host='localhost',
            database='mydb',
            port=1433,
            username='myuser',
            password='password',
            ca_path='/test/cert.ca',
            timeout=20
        )
        self.assertIs(conn, self.conn_mock)
        gcp_cloud_sql_connector_mock.get.assert_called_once_with(self.creds_path)
        self.connector_mock.connect.assert_called_once_with(
            'localhost',
            driver='pytds',
            user='myuser',
            password='password',
            db='mydb',
            ip_type=IPTypes.PUBLIC,
            cafile='/test/cert.ca',
            validate_host=False,
            timeout=20,
            port=1433
        )

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.sqlserver.gcp_pytds_adapter.GcpCloudSqlConnector')
    def test_connect_forwards_default(self, gcp_cloud_sql_connector_mock):
        gcp_cloud_sql_connector_mock.get.return_value = self.connector_mock
        conn = self.adapter.connect(
            host='localhost',
            database='mydb'
        )
        self.assertIs(conn, self.conn_mock)
        gcp_cloud_sql_connector_mock.get.assert_called_once_with(self.creds_path)
        self.connector_mock.connect.assert_called_once_with(
            'localhost',
            driver='pytds',
            user=None,
            password=None,
            db='mydb',
            ip_type=IPTypes.PUBLIC,
            cafile=None,
            validate_host=False,
            timeout=10,
            port=None
        )