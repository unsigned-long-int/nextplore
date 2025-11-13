import unittest
from unittest.mock import MagicMock

from nextplore_sdk.database.connection_maker.credentials_providers.snowflake_secret_credentials_provider import \
    SnowflakeSecretCredentialsProvider


class TestSnowflakeSecretCredentialsProvider(unittest.TestCase):
    def setUp(self):
        self.profile = MagicMock()
        self.profile.client_secret = 'client_secret'
        self.credentials_provider = SnowflakeSecretCredentialsProvider(profile=self.profile)

    def test_returns_client_secret(self):
        creds = self.credentials_provider.creds()
        self.assertEqual(creds, 'client_secret')