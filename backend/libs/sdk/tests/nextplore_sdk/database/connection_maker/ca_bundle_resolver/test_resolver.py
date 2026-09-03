import os
import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.ca_bundle_resolver.resolver import (
    resolve_ca_bundle,
)


class TestResolver(unittest.TestCase):
    @patch.dict(os.environ, {"NEXTPLORE_CA_BUNDLE": "test.pem"}, clear=True)
    def test_returns_env_ca(self):
        ca_bundle = resolve_ca_bundle()
        self.assertEqual(ca_bundle, "test.pem")

    @patch("ssl.get_default_verify_paths")
    @patch("os.path")
    def test_returns_default_path_for_ssl(self, os_path_mock, ssl_mock):
        file_item = MagicMock()
        file_item.cafile = "test.pem"
        os_path_mock.isfile.return_value = True
        ssl_mock.return_value = file_item
        ca_bundle = resolve_ca_bundle()
        self.assertEqual(ca_bundle, "test.pem")

    @patch("ssl.get_default_verify_paths")
    @patch("certifi.where")
    def test_returns_certifi_last_resort(self, certifi_mock, ssl_mock):
        file_item = MagicMock()
        file_item.cafile = None
        ssl_mock.return_value = file_item
        certifi_mock.return_value = "certifi-test.pem"
        ca_bundle = resolve_ca_bundle()
        self.assertEqual(ca_bundle, "certifi-test.pem")
