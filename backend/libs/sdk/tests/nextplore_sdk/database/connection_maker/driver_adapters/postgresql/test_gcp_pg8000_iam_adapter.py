import unittest
from unittest.mock import MagicMock, patch


from nextplore_sdk.database.connection_maker.driver_adapters.postgresql.gcp_pg8000_iam_adapter import \
    GcpPostgresqlPg8000IamAdapter, IPTypes


class TestGcpPostgresqlPg8000IamAdapter(unittest.TestCase):
    def setUp(self):
        self.cred_path = '/Users/nik/Downloads/nextplore-470323-18ec66288496.json'
        self.adapter = GcpPostgresqlPg8000IamAdapter()

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.postgresql.gcp_pg8000_iam_adapter.GcpCloudSqlConnector')
    def test_connect_happy_path(self, gcp_cloud_sql_connector_mock):
        connector_mock = MagicMock()
        conn_mock = MagicMock()
        connector_mock.connect.return_value = conn_mock
        gcp_cloud_sql_connector_mock.get.return_value = connector_mock
        conn = self.adapter.connect(
            host='localhost',
            database='mydb',
            port=5432,
            username='user',
            password='password',
            ca_path='/test.ca',
            timeout=20
        )
        gcp_cloud_sql_connector_mock.get.assert_called_once_with(self.cred_path)
        connector_mock.connect.assert_called_once_with(
            'localhost',
            driver='pg8000',
            user='user',
            db='mydb',
            enable_iam_auth=True,
            ip_type=IPTypes.PUBLIC,
            timeout=20,
            port=5432
        )
        self.assertIs(conn, conn_mock)

    @patch('nextplore_sdk.database.connection_maker.driver_adapters.postgresql.gcp_pg8000_iam_adapter.GcpCloudSqlConnector')
    def test_connect_forwards_default(self, gcp_cloud_sql_connector_mock):
        connector_mock = MagicMock()
        conn_mock = MagicMock()
        connector_mock.connect.return_value = conn_mock
        gcp_cloud_sql_connector_mock.get.return_value = connector_mock
        conn = self.adapter.connect(
            host='localhost',
            database='mydb'
        )
        gcp_cloud_sql_connector_mock.get.assert_called_once_with(self.cred_path)
        connector_mock.connect.assert_called_once_with(
            'localhost',
            driver='pg8000',
            user=None,
            db='mydb',
            enable_iam_auth=True,
            ip_type=IPTypes.PUBLIC,
            timeout=10,
            port=None
        )
        self.assertIs(conn, conn_mock)
