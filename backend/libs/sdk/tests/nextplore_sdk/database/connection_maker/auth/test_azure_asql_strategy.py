import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.auth.azure_asql_strategy import (
    AzureIamAsqlStrategy,
)


class TestAzureIamAsqlStrategy(unittest.TestCase):
    def setUp(self):
        self.profile = MagicMock()
        self.strategy = AzureIamAsqlStrategy(self.profile)

    @patch(
        "nextplore_sdk.database.connection_maker.auth.azure_asql_strategy.make_token_bytes"
    )
    @patch(
        "nextplore_sdk.database.connection_maker.auth.azure_asql_strategy.resolve_ca_bundle"
    )
    def test_makes_creator_with_creds_provider(
        self, resolve_ca_bundle_mock, make_token_bytes_mock
    ):
        resolve_ca_bundle_mock.return_value = "ca_bundle.pem"
        creds_provider_mock = MagicMock()
        driver_adapter_mock = MagicMock()
        make_token_bytes_mock.return_value = b""
        creds_provider_mock.creds.return_value = "credential"
        creator = self.strategy.make_creator(
            adapter=driver_adapter_mock, creds_provider=creds_provider_mock
        )
        creator()
        make_token_bytes_mock.assert_called_once_with("credential")
        creds_provider_mock.creds.assert_called_once_with(scope=self.strategy.SCOPE)
        driver_adapter_mock.connect.assert_called_once_with(
            host=self.profile.host,
            port=self.profile.port,
            database=self.profile.database,
            ca_path="ca_bundle.pem",
            attrs_before={self.strategy.ACCESS_TOKEN_ATTR: b""},
        )

    def test_raises_exception_when_no_creds_provided(self):
        driver_adapter_mock = MagicMock()
        with self.assertRaises(KeyError) as context:
            self.strategy.make_creator(driver_adapter_mock)
        self.assertIn("Creds provider is not given", str(context.exception))
