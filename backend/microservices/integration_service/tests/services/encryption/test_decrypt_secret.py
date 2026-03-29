import unittest
from unittest.mock import Mock

from integration_service.domain.models.secret import SecretType, DataStoreSecret
from integration_service.services.encryption import decrypt_secret
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient


class TestDecryptSecret(unittest.TestCase):

    def setUp(self):
        self.mock_crypto_client = Mock(spec=CryptoClient)

    def test_decrypt_secret_when_secret_exists(self):
        secret_type = SecretType.USERNAME
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = 'decrypted_api_key_value'

        secrets = {
            SecretType.USERNAME: mock_secret
        }

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertEqual(result, 'decrypted_api_key_value')
        mock_secret.reveal.assert_called_once_with(self.mock_crypto_client)

    def test_decrypt_secret_when_secret_does_not_exist(self):
        secret_type = SecretType.CLIENT_SECRET
        secrets = {}

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertIsNone(result)

    def test_decrypt_secret_when_secret_type_not_in_dict(self):
        secret_type = SecretType.PASSWORD
        secrets = {
            SecretType.USERNAME: Mock(spec=DataStoreSecret)
        }

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertIsNone(result)

    def test_decrypt_secret_with_multiple_secrets(self):
        mock_api_key_secret = Mock(spec=DataStoreSecret)
        mock_api_key_secret.reveal.return_value = 'api_key_value'

        mock_password_secret = Mock(spec=DataStoreSecret)
        mock_password_secret.reveal.return_value = 'password_value'

        mock_token_secret = Mock(spec=DataStoreSecret)
        mock_token_secret.reveal.return_value = 'token_value'

        secrets = {
            SecretType.CLIENT_SECRET: mock_api_key_secret,
            SecretType.PASSWORD: mock_password_secret,
            SecretType.USERNAME: mock_token_secret
        }

        result = decrypt_secret(SecretType.PASSWORD, secrets, self.mock_crypto_client)

        self.assertEqual(result, 'password_value')
        mock_password_secret.reveal.assert_called_once_with(self.mock_crypto_client)
        mock_api_key_secret.reveal.assert_not_called()
        mock_token_secret.reveal.assert_not_called()

    def test_decrypt_secret_passes_crypto_client_to_reveal(self):
        secret_type = SecretType.CLIENT_SECRET
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = 'decrypted_token'

        secrets = {SecretType.CLIENT_SECRET: mock_secret}

        decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        mock_secret.reveal.assert_called_once_with(self.mock_crypto_client)

    def test_decrypt_secret_with_empty_string_result(self):
        secret_type = SecretType.PASSWORD
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = ''

        secrets = {SecretType.PASSWORD: mock_secret}

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertEqual(result, '')
        self.assertIsNotNone(result)

    def test_decrypt_secret_with_special_characters(self):
        secret_type = SecretType.PASSWORD
        special_password = "P@ssw0rd!#$%^&*(){}[]|\\:;\''<>,.?/~`"
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = special_password

        secrets = {SecretType.PASSWORD: mock_secret}

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertEqual(result, special_password)

    def test_decrypt_secret_with_unicode_characters(self):
        secret_type = SecretType.USERNAME
        unicode_token = '秘密tok'
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = unicode_token

        secrets = {SecretType.USERNAME: mock_secret}

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertEqual(result, unicode_token)

    def test_decrypt_secret_reveal_raises_exception(self):
        secret_type = SecretType.PASSWORD
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.side_effect = Exception('Decryption failed')

        secrets = {SecretType.PASSWORD: mock_secret}

        with self.assertRaises(Exception) as context:
            decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertEqual(str(context.exception), 'Decryption failed')

    def test_decrypt_secret_with_none_value_in_dict(self):
        secret_type = SecretType.PASSWORD
        secrets = {SecretType.PASSWORD: None}

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertIsNone(result)

    def test_decrypt_secret_called_exactly_once(self):
        secret_type = SecretType.PASSWORD
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = 'password'

        secrets = {SecretType.PASSWORD: mock_secret}

        decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertEqual(mock_secret.reveal.call_count, 1)

    def test_decrypt_secret_return_type(self):
        secret_type = SecretType.CLIENT_SECRET
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = 'token_value'

        secrets = {SecretType.CLIENT_SECRET: mock_secret}

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertIsInstance(result, str)

    def test_decrypt_secret_with_different_secret_types(self):
        secret_types_to_test = [
            SecretType.CLIENT_SECRET,
            SecretType.PASSWORD,
            SecretType.USERNAME,
        ]

        for secret_type in secret_types_to_test:
            with self.subTest(secret_type=secret_type):
                mock_secret = Mock(spec=DataStoreSecret)
                expected_value = f'decrypted_{secret_type.value}'
                mock_secret.reveal.return_value = expected_value

                secrets = {secret_type: mock_secret}

                result = decrypt_secret(
                    secret_type,
                    secrets,
                    self.mock_crypto_client
                )

                self.assertEqual(result, expected_value)

    def test_decrypt_secret_does_not_modify_input_dict(self):
        secret_type = SecretType.CLIENT_SECRET
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = 'api_key'

        secrets = {SecretType.CLIENT_SECRET: mock_secret}
        original_secrets = secrets.copy()

        decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertEqual(secrets, original_secrets)

    def test_decrypt_secret_with_long_decrypted_value(self):
        secret_type = SecretType.CLIENT_SECRET
        long_token = 'a' * 10000
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = long_token

        secrets = {SecretType.CLIENT_SECRET: mock_secret}

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertEqual(result, long_token)
        self.assertEqual(len(result), 10000)


class TestDecryptSecretEdgeCases(unittest.TestCase):

    def setUp(self):
        self.mock_crypto_client = Mock(spec=CryptoClient)

    def test_decrypt_secret_with_whitespace_only_value(self):
        secret_type = SecretType.PASSWORD
        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = '   \t\n  '

        secrets = {SecretType.PASSWORD: mock_secret}

        result = decrypt_secret(secret_type, secrets, self.mock_crypto_client)

        self.assertEqual(result, '   \t\n  ')

    def test_decrypt_secret_crypto_client_is_used_correctly(self):
        secret_type = SecretType.CLIENT_SECRET
        specific_crypto_client = Mock(spec=CryptoClient)
        specific_crypto_client.unique_id = 'test-crypto-123'

        mock_secret = Mock(spec=DataStoreSecret)
        mock_secret.reveal.return_value = 'decrypted'

        secrets = {SecretType.CLIENT_SECRET: mock_secret}

        decrypt_secret(secret_type, secrets, specific_crypto_client)

        call_args = mock_secret.reveal.call_args
        passed_client = call_args[0][0]
        self.assertIs(passed_client, specific_crypto_client)
