import unittest
from unittest.mock import MagicMock

from nextplore_sdk.database.connection_maker.credentials_providers.snowflake_private_key_credentials_provider import \
    SnowflakePrivateKeyCredentialsProvider


class TestSnowflakePrivateKeyCredentials(unittest.TestCase):
    def setUp(self):
        self.profile = MagicMock()
        self.profile.snowflake_private_key = 'snowflake_private_key'
        self.credentials_provider = SnowflakePrivateKeyCredentialsProvider(self.profile)

    def test_returns_private_key(self):
        creds = self.credentials_provider.creds()
        self.assertEqual(creds, 'snowflake_private_key')