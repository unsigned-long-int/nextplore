import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.credentials_providers.azure_secret_credentials_provider import (
    AzureSecretCredentialsProvider,
)


class TestAzureSecretCredentialsProvider(unittest.TestCase):
    def setUp(self):
        self.profile = MagicMock()
        self.credentials_provider = AzureSecretCredentialsProvider(self.profile)

    @patch(
        "nextplore_sdk.database.connection_maker.credentials_providers.azure_secret_credentials_provider.ClientSecretCredential"
    )
    def test_sets_default_scope_if_not_provided(self, client_secret_credential_mock):
        cred_mock = MagicMock()
        token_mock = MagicMock()
        token_mock.token = "token"
        cred_mock.get_token.return_value = token_mock
        client_secret_credential_mock.return_value = cred_mock
        creds = self.credentials_provider.creds()
        cred_mock.get_token.assert_called_with(self.credentials_provider.DEFAULT_SCOPE)
        self.assertEqual(creds, token_mock.token)

    @patch(
        "nextplore_sdk.database.connection_maker.credentials_providers.azure_secret_credentials_provider.ClientSecretCredential"
    )
    def test_sets_default_scope_if_provided(self, client_secret_credential_mock):
        cred_mock = MagicMock()
        token_mock = MagicMock()
        token_mock.token = "token"
        cred_mock.get_token.return_value = token_mock
        client_secret_credential_mock.return_value = cred_mock
        creds = self.credentials_provider.creds(scope="custom-scope")
        cred_mock.get_token.assert_called_with("custom-scope")
        self.assertEqual(creds, token_mock.token)
