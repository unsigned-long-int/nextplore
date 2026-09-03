import unittest
from collections.abc import Callable
from unittest.mock import MagicMock, patch

from nextplore_sdk.encryptor.client.azure_crypto_client import AzureCryptoClient
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from nextplore_sdk.encryptor.client.crypto_client_factory import (
    CRYPTO_CLIENTS_REGISTRY,
    get_crypto_client,
)


class TestGetCryptoClient(unittest.TestCase):
    def test_returns_callable(self):
        result = get_crypto_client("azure")

        self.assertTrue(callable(result))
        self.assertIsInstance(result, Callable)

    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_default_client_is_azure(self, mock_credential, mock_crypto_client):
        factory = get_crypto_client()

        client = factory("test-kek-kid")
        self.assertIsInstance(client, AzureCryptoClient)

    def test_azure_client_explicitly(self):
        factory = get_crypto_client("azure")

        self.assertTrue(callable(factory))

    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_factory_creates_azure_client(self, mock_credential, mock_crypto_client):
        kek_kid = "https://test-vault.vault.azure.net/keys/test-key/version"

        factory = get_crypto_client("azure")
        client = factory(kek_kid)

        self.assertIsInstance(client, AzureCryptoClient)

    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_factory_passes_kek_kid_to_client(
        self, mock_credential, mock_crypto_client
    ):
        kek_kid = "https://test-vault.vault.azure.net/keys/test-key/version"

        factory = get_crypto_client("azure")
        factory(kek_kid)

        mock_crypto_client.assert_called_once()
        call_args = mock_crypto_client.call_args
        self.assertEqual(call_args[0][0], kek_kid)

    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_different_kek_kids_create_different_instances(
        self, mock_credential, mock_crypto_client
    ):
        kek_kid_1 = "https://vault1.vault.azure.net/keys/key1/v1"
        kek_kid_2 = "https://vault2.vault.azure.net/keys/key2/v2"

        factory = get_crypto_client("azure")
        client1 = factory(kek_kid_1)
        client2 = factory(kek_kid_2)

        self.assertIsInstance(client1, AzureCryptoClient)
        self.assertIsInstance(client2, AzureCryptoClient)
        self.assertIsNot(client1, client2)

    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_factory_can_be_called_multiple_times(
        self, mock_credential, mock_crypto_client
    ):
        kek_kid = "https://test-vault.vault.azure.net/keys/test-key/version"
        factory = get_crypto_client("azure")

        client1 = factory(kek_kid)
        client2 = factory(kek_kid)

        self.assertIsInstance(client1, AzureCryptoClient)
        self.assertIsInstance(client2, AzureCryptoClient)
        self.assertIsNot(client1, client2)

    def test_unknown_client_returns_none_factory(self):
        factory = get_crypto_client("unknown_client")

        self.assertTrue(callable(factory))

        with self.assertRaises(TypeError):
            factory("some-kek-kid")

    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_client_implements_crypto_client_interface(
        self, mock_credential, mock_crypto_client
    ):
        kek_kid = "https://test-vault.vault.azure.net/keys/test-key/version"

        factory = get_crypto_client("azure")
        client = factory(kek_kid)

        self.assertIsInstance(client, CryptoClient)
        self.assertTrue(hasattr(client, "encrypt_secret"))
        self.assertTrue(hasattr(client, "decrypt_secret"))

    def test_registry_contains_azure_client(self):
        self.assertIn("azure", CRYPTO_CLIENTS_REGISTRY)
        self.assertEqual(CRYPTO_CLIENTS_REGISTRY["azure"], AzureCryptoClient)

    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_get_client_uses_registry(self, mock_credential, mock_crypto_client):
        kek_kid = "test-kek-kid"

        factory = get_crypto_client("azure")

        expected_class = CRYPTO_CLIENTS_REGISTRY["azure"]
        client = factory(kek_kid)
        self.assertIsInstance(client, expected_class)

    def test_empty_string_client_type(self):
        factory = get_crypto_client("")

        self.assertTrue(callable(factory))

        with self.assertRaises(TypeError):
            factory("some-kek-kid")

    def test_none_client_type(self):
        factory = get_crypto_client(None)

        self.assertTrue(callable(factory))

        with self.assertRaises(TypeError):
            factory("some-kek-kid")

    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_case_sensitive_client_type(self, mock_credential, mock_crypto_client):
        factory_lowercase = get_crypto_client("azure")
        factory_uppercase = get_crypto_client("AZURE")

        client_lowercase = factory_lowercase("test-kek-kid")
        self.assertIsInstance(client_lowercase, AzureCryptoClient)

        with self.assertRaises(TypeError):
            factory_uppercase("test-kek-kid")


class TestGetCryptoClientWithMocking(unittest.TestCase):
    def setUp(self):
        self.mock_client_class = MagicMock(spec=CryptoClient)
        self.mock_instance = MagicMock(spec=CryptoClient)
        self.mock_client_class.return_value = self.mock_instance

    @patch.dict(CRYPTO_CLIENTS_REGISTRY, {"azure": MagicMock()})
    def test_factory_with_mocked_registry(self):
        mock_azure_class = CRYPTO_CLIENTS_REGISTRY["azure"]
        mock_instance = MagicMock(spec=CryptoClient)
        mock_azure_class.return_value = mock_instance

        kek_kid = "test-kek-kid"

        factory = get_crypto_client("azure")
        result = factory(kek_kid)

        mock_azure_class.assert_called_once_with(kek_kid)
        self.assertEqual(result, mock_instance)

    @patch.dict(CRYPTO_CLIENTS_REGISTRY, {"test": MagicMock()}, clear=False)
    def test_custom_client_in_registry(self):
        mock_test_class = CRYPTO_CLIENTS_REGISTRY["test"]
        mock_instance = MagicMock(spec=CryptoClient)
        mock_test_class.return_value = mock_instance

        kek_kid = "test-kek-kid"

        factory = get_crypto_client("test")
        result = factory(kek_kid)

        mock_test_class.assert_called_once_with(kek_kid)
        self.assertEqual(result, mock_instance)


class TestCryptoClientsRegistry(unittest.TestCase):
    def test_registry_is_dict(self):
        self.assertIsInstance(CRYPTO_CLIENTS_REGISTRY, dict)

    def test_registry_not_empty(self):
        self.assertGreater(len(CRYPTO_CLIENTS_REGISTRY), 0)

    def test_registry_keys_are_strings(self):
        for key in CRYPTO_CLIENTS_REGISTRY:
            self.assertIsInstance(key, str)

    def test_registry_values_are_classes(self):
        for value in CRYPTO_CLIENTS_REGISTRY.values():
            self.assertTrue(isinstance(value, type))

    def test_registry_values_are_crypto_client_subclasses(self):
        for client_class in CRYPTO_CLIENTS_REGISTRY.values():
            self.assertTrue(issubclass(client_class, CryptoClient))


class TestGetCryptoClientIntegration(unittest.TestCase):
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_full_workflow_azure_client(self, mock_credential, mock_crypto_client):
        kek_kid = "https://test-vault.vault.azure.net/keys/test-key/version"

        factory = get_crypto_client("azure")
        client = factory(kek_kid)

        self.assertIsInstance(client, AzureCryptoClient)
        self.assertIsInstance(client, CryptoClient)

        self.assertTrue(callable(client.encrypt_secret))
        self.assertTrue(callable(client.decrypt_secret))

    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient")
    @patch("nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential")
    def test_factory_pattern_consistency(self, mock_credential, mock_crypto_client):
        kek_kid_1 = "kek-kid-1"
        kek_kid_2 = "kek-kid-2"

        factory1 = get_crypto_client("azure")
        factory2 = get_crypto_client("azure")

        client1a = factory1(kek_kid_1)
        client1b = factory1(kek_kid_2)
        client2a = factory2(kek_kid_1)

        self.assertIsNot(client1a, client1b)
        self.assertIsNot(client1a, client2a)
        self.assertIsNot(client1b, client2a)

        self.assertIsInstance(client1a, AzureCryptoClient)
        self.assertIsInstance(client1b, AzureCryptoClient)
        self.assertIsInstance(client2a, AzureCryptoClient)

    def test_lambda_captures_correct_client_class(self):
        original_azure = CRYPTO_CLIENTS_REGISTRY["azure"]

        mock_client_class = MagicMock(spec=CryptoClient)
        mock_instance = MagicMock(spec=CryptoClient)
        mock_client_class.return_value = mock_instance

        try:
            factory_before = get_crypto_client("azure")

            CRYPTO_CLIENTS_REGISTRY["azure"] = mock_client_class

            factory_after = get_crypto_client("azure")

            client_after = factory_after("test-kek-kid")
            self.assertEqual(client_after, mock_instance)
            mock_client_class.assert_called_once_with("test-kek-kid")

            with patch(
                "nextplore_sdk.encryptor.client.azure_crypto_client.CryptographyClient"
            ):
                with patch(
                    "nextplore_sdk.encryptor.client.azure_crypto_client.DefaultAzureCredential"
                ):
                    client_before = factory_before("test-kek-kid")
                    self.assertIsInstance(client_before, original_azure)

        finally:
            CRYPTO_CLIENTS_REGISTRY["azure"] = original_azure


class TestGetCryptoClientEdgeCases(unittest.TestCase):
    def test_special_characters_in_client_type(self):
        factory = get_crypto_client("azure-test-123")

        self.assertTrue(callable(factory))

        with self.assertRaises(TypeError):
            factory("kek-kid")

    def test_whitespace_in_client_type(self):
        factory = get_crypto_client(" azure ")

        self.assertTrue(callable(factory))

        with self.assertRaises(TypeError):
            factory("kek-kid")

    def test_numeric_client_type(self):
        factory = get_crypto_client("123")

        self.assertTrue(callable(factory))

        with self.assertRaises(TypeError):
            factory("kek-kid")
