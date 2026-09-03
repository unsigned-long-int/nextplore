import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.driver_adapters.mysql.gcp_pymysql_iam_adapter import (
    GcpMysqlPyMysqlIamAdapter,
    IPTypes,
)


class TestGcpMysqlPyMysqlIamAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = GcpMysqlPyMysqlIamAdapter()
        self.creds_path = "/Users/nik/Downloads/nextplore-470323-18ec66288496.json"
        self.instance = "project:region:instance"

    @patch(
        "nextplore_sdk.database.connection_maker.driver_adapters.mysql.gcp_pymysql_iam_adapter.GcpCloudSqlConnector"
    )
    def test_connect_happy_path(self, gcp_cloud_sql_connector_mock):
        fake_conn = object()
        connector_instance = MagicMock()
        connector_instance.connect.return_value = fake_conn
        gcp_cloud_sql_connector_mock.get.return_value = connector_instance

        result = self.adapter.connect(
            host=self.instance,
            database="mydb",
            port=3306,
            username="user",
            password="pass",
            timeout=20,
        )

        gcp_cloud_sql_connector_mock.get.assert_called_once()
        connector_instance.connect.assert_called_once_with(
            self.instance,
            driver="pymysql",
            user="user",
            db="mydb",
            enable_iam_auth=True,
            ip_type=IPTypes.PUBLIC,
            timeout=20,
            port=3306,
        )
        self.assertIs(result, fake_conn)

    @patch(
        "nextplore_sdk.database.connection_maker.driver_adapters.mysql.gcp_pymysql_iam_adapter.GcpCloudSqlConnector"
    )
    def test_connect_forwards_defaults(self, gcp_cloud_sql_connector_mock):
        connector_instance = MagicMock()
        connector_instance.connect.return_value = "conn"
        gcp_cloud_sql_connector_mock.get.return_value = connector_instance

        _ = self.adapter.connect(
            host=self.instance,
            database="mydb",
        )

        connector_instance.connect.assert_called_once_with(
            self.instance,
            driver="pymysql",
            user=None,
            db="mydb",
            enable_iam_auth=True,
            ip_type=IPTypes.PUBLIC,
            timeout=10,
            port=None,
        )

    @patch(
        "nextplore_sdk.database.connection_maker.driver_adapters.mysql.gcp_pymysql_iam_adapter.GcpCloudSqlConnector"
    )
    def test_connect_propagates_exception(self, gcp_cloud_sql_connector_mock):
        connector_instance = MagicMock()
        connector_instance.connect.side_effect = RuntimeError("boom")
        gcp_cloud_sql_connector_mock.get.return_value = connector_instance

        with self.assertRaisesRegex(RuntimeError, "boom"):
            self.adapter.connect(host=self.instance, database="mydb")
