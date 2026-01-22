import unittest
from unittest.mock import MagicMock

from nextplore_sdk.database.connection_maker.auth.snowflake_jwt_auth_strategy import SnowflakeJwtAuthStrategy


class TestSnowflakeJwtAuthStrategy(unittest.TestCase):
    def setUp(self):
        self.profile = MagicMock()
        self.strategy = SnowflakeJwtAuthStrategy(self.profile)

    def test_makes_creator_with_creds_provider(self):
        creds_provider_mock = MagicMock()
        driver_adapter_mock = MagicMock()
        creds_provider_mock.creds.return_value = 'snowflake-private-key'
        creator = self.strategy.make_creator(
            adapter=driver_adapter_mock,
            creds_provider=creds_provider_mock
        )
        creator()
        creds_provider_mock.creds.assert_called_once_with()
        creds_provider_mock.creds.assert_called_once_with()
        driver_adapter_mock.connect.assert_called_once_with(
            host=self.profile.host,
            database=self.profile.database,
            username=self.profile.username,
            private_key='snowflake-private-key',
            warehouse=self.profile.warehouse
        )

    def test_raises_exception_when_no_creds_provided(self):
        driver_adapter_mock = MagicMock()
        with self.assertRaises(KeyError) as context:
            self.strategy.make_creator(driver_adapter_mock)
        self.assertIn('Credentials provider not found', str(context.exception))
