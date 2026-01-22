import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.auth.credential_auth_strategy import CredentialAuthStrategy


class TestAzureIamAsqlStrategy(unittest.TestCase):
    def setUp(self):
        self.profile = MagicMock()
        self.strategy = CredentialAuthStrategy(self.profile)

    @patch('nextplore_sdk.database.connection_maker.auth.credential_auth_strategy.resolve_ca_bundle')
    def test_makes_creator_with_creds_provider(
        self,
        resolve_ca_bundle_mock
    ):
        resolve_ca_bundle_mock.return_value = 'ca_bundle.pem'
        creds_provider_mock = MagicMock()
        driver_adapter_mock = MagicMock()
        creds_provider_mock.creds.return_value = 'credential'
        creator = self.strategy.make_creator(
            adapter=driver_adapter_mock,
            creds_provider=creds_provider_mock
        )
        creator()
        creds_provider_mock.creds.assert_called_once_with()
        driver_adapter_mock.connect.assert_called_once_with(
            host=self.profile.host,
            port=self.profile.port,
            database=self.profile.database,
            username=self.profile.username,
            password='credential',
            ca_path='ca_bundle.pem',
            timeout=10
        )

    def test_raises_exception_when_no_creds_provided(self):
        driver_adapter_mock = MagicMock()
        with self.assertRaises(KeyError) as context:
            self.strategy.make_creator(driver_adapter_mock)
        self.assertIn('Credentials provider not found', str(context.exception))
