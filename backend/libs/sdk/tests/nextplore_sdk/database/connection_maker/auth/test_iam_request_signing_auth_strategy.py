import unittest
from unittest.mock import MagicMock

from nextplore_sdk.database.connection_maker.auth.iam_request_signing_auth_strategy import (
    IamRequestSigningAuthStrategy,
)


class TestIamRequestSigningAuthStrategy(unittest.TestCase):
    def setUp(self):
        self.profile = MagicMock()
        self.strategy = IamRequestSigningAuthStrategy(self.profile)

    def test_makes_creator_without_creds_provider(self):
        driver_adapter_mock = MagicMock()
        creator = self.strategy.make_creator(adapter=driver_adapter_mock)
        creator()
        driver_adapter_mock.connect.assert_called_once_with(
            host=self.profile.host,
            port=self.profile.port,
            database=self.profile.database,
            username=self.profile.username,
        )
