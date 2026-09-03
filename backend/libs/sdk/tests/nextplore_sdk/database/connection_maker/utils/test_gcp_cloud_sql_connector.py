import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.utils.gcp_cloud_sql_connector import (
    GcpCloudSqlConnector,
)


class TestGcpCloudSqlConnector(unittest.TestCase):
    def setUp(self):
        self.sql_connector = GcpCloudSqlConnector()

    @patch(
        "nextplore_sdk.database.connection_maker.utils.gcp_cloud_sql_connector.Connector"
    )
    @patch(
        "nextplore_sdk.database.connection_maker.utils.gcp_cloud_sql_connector.service_account"
    )
    def test_build_connector_if_not_existing(
        self, service_account_mock, connector_mock
    ):
        creds_mock = MagicMock()
        connector_instance_mock = MagicMock()
        connector_mock.return_value = connector_instance_mock
        service_account_mock.Credentials.from_service_account_file.return_value = (
            creds_mock
        )
        credentials_path = "/path/to/credentials.json"

        connector = self.sql_connector.get(credentials_path)
        self.assertIs(connector, connector_instance_mock)
        service_account_mock.Credentials.from_service_account_file.assert_called_once_with(
            credentials_path
        )
        connector_mock.assert_called_once_with(credentials=creds_mock)

    @patch(
        "nextplore_sdk.database.connection_maker.utils.gcp_cloud_sql_connector.Connector"
    )
    @patch(
        "nextplore_sdk.database.connection_maker.utils.gcp_cloud_sql_connector.service_account"
    )
    def test_closes_and_returns_initial_instance_connector_if_existing(
        self, service_account_mock, connector_mock
    ):
        self.sql_connector.close()
        creds_mock = MagicMock()
        first_connector_instance_mock = MagicMock()
        connector_mock.return_value = first_connector_instance_mock
        service_account_mock.Credentials.from_service_account_file.return_value = (
            creds_mock
        )
        credentials_path = "/path/to/credentials.json"

        first_connector = self.sql_connector.get(credentials_path)
        self.assertIs(first_connector, first_connector_instance_mock)
        service_account_mock.Credentials.from_service_account_file.assert_called_once_with(
            credentials_path
        )
        connector_mock.assert_called_once_with(credentials=creds_mock)

        second_connector_instance_mock = MagicMock()
        connector_mock.return_value = second_connector_instance_mock
        service_account_mock.Credentials.from_service_account_file.return_value = (
            creds_mock
        )

        second_connector = self.sql_connector.get(credentials_path)
        self.assertIs(second_connector, first_connector_instance_mock)
        self.assertEqual(
            service_account_mock.Credentials.from_service_account_file.call_count, 1
        )
