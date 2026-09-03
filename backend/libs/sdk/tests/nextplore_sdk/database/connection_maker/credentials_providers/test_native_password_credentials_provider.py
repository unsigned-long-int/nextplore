import unittest
from unittest.mock import MagicMock

from nextplore_sdk.database.connection_maker.credentials_providers.native_password_credentials_provider import (
    NativePasswordCredentialsProvider,
)


class TestNativePasswordCredentialsProvider(unittest.TestCase):
    def setUp(self):
        self.profile = MagicMock()
        self.profile.password = "password"
        self.credentials_provider = NativePasswordCredentialsProvider(self.profile)

    def test_returns_profile_password(self):
        creds = self.credentials_provider.creds()
        self.assertEqual(creds, "password")
