import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID, uuid4

from integration_service.domain.models.secret import DataStoreSecret
from integration_service.services.encryption import encrypt_secret, encrypt_conn_params
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from nextplore_sdk.encryptor.client.encrypted_secret import EncryptedSecret



class TestEncryptSecret(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.datastore_id = uuid4()
        self.plaintext = 'my_secret_password'

        self.mock_crypto_client = Mock(spec=CryptoClient)

        self.mock_encrypted_result = Mock()
        self.mock_encrypted_result.ciphertext = b'encrypted_data'
        self.mock_encrypted_result.nonce = b'random_nonce'
        self.mock_encrypted_result.tag = b'auth_tag'
        self.mock_encrypted_result.wrapped_dek = b'wrapped_key'

        self.mock_crypto_client.encrypt_secret.return_value = self.mock_encrypted_result

    def test_encrypt_secret_basic_functionality(self):
        result = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=self.plaintext,
            crypto_client=self.mock_crypto_client
        )

        self.assertIsInstance(result, DataStoreSecret)
        self.assertEqual(result.organization_id, self.organization_id)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.datastore_id, self.datastore_id)
        self.assertEqual(result.ciphertext, b'encrypted_data')
        self.assertEqual(result.nonce, b'random_nonce')
        self.assertEqual(result.tag, b'auth_tag')
        self.assertEqual(result.wrapped_dek, b'wrapped_key')

    def test_encrypt_secret_calls_crypto_client_with_correct_params(self):
        encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=self.plaintext,
            crypto_client=self.mock_crypto_client
        )

        self.mock_crypto_client.encrypt_secret.assert_called_once_with(
            plaintext=self.plaintext,
            aad={
                'organization_id': self.organization_id,
                'user_id': self.user_id,
                'datastore_id': self.datastore_id
            }
        )

    def test_encrypt_secret_with_additional_kwargs(self):
        additional_kwargs = {
            'secret_name': 'api_key',
            'description': 'Production API key',
            'expires_at': '2025-12-31'
        }

        with patch('integration_service.services.encryption.encrypt_secret.DataStoreSecret') as mock_secret_class:
            mock_secret_instance = Mock()
            mock_secret_class.return_value = mock_secret_instance

            _ = encrypt_secret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                plaintext=self.plaintext,
                crypto_client=self.mock_crypto_client,
                **additional_kwargs
            )

            mock_secret_class.assert_called_once_with(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                ciphertext=self.mock_encrypted_result.ciphertext,
                nonce=self.mock_encrypted_result.nonce,
                tag=self.mock_encrypted_result.tag,
                wrapped_dek=self.mock_encrypted_result.wrapped_dek,
                secret_name='api_key',
                description='Production API key',
                expires_at='2025-12-31'
            )

    def test_encrypt_secret_with_empty_string(self):
        empty_plaintext = ''

        _ = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=empty_plaintext,
            crypto_client=self.mock_crypto_client
        )

        self.mock_crypto_client.encrypt_secret.assert_called_once()
        call_args = self.mock_crypto_client.encrypt_secret.call_args
        self.assertEqual(call_args[1]['plaintext'], '')

    def test_encrypt_secret_with_special_characters(self):
        special_plaintext = "P@ssw0rd!#$%^&*(){}[]|\\:;\''<>,.?/~`"

        _ = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=special_plaintext,
            crypto_client=self.mock_crypto_client
        )

        call_args = self.mock_crypto_client.encrypt_secret.call_args
        self.assertEqual(call_args[1]['plaintext'], special_plaintext)

    def test_encrypt_secret_with_unicode_characters(self):
        unicode_plaintext = '秘密password'

        _ = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=unicode_plaintext,
            crypto_client=self.mock_crypto_client
        )

        call_args = self.mock_crypto_client.encrypt_secret.call_args
        self.assertEqual(call_args[1]['plaintext'], unicode_plaintext)

    def test_encrypt_secret_with_very_long_plaintext(self):
        long_plaintext = 'a' * 100000

        _ = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=long_plaintext,
            crypto_client=self.mock_crypto_client
        )

        call_args = self.mock_crypto_client.encrypt_secret.call_args
        self.assertEqual(call_args[1]['plaintext'], long_plaintext)

    def test_encrypt_secret_aad_structure(self):
        encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=self.plaintext,
            crypto_client=self.mock_crypto_client
        )

        call_args = self.mock_crypto_client.encrypt_secret.call_args
        aad = call_args[1]['aad']

        self.assertIsInstance(aad, dict)
        self.assertEqual(len(aad), 3)
        self.assertIn('organization_id', aad)
        self.assertIn('user_id', aad)
        self.assertIn('datastore_id', aad)
        self.assertIsInstance(aad['organization_id'], UUID)
        self.assertIsInstance(aad['user_id'], UUID)
        self.assertIsInstance(aad['datastore_id'], UUID)

    def test_encrypt_secret_preserves_uuid_objects_in_aad(self):
        encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=self.plaintext,
            crypto_client=self.mock_crypto_client
        )

        call_args = self.mock_crypto_client.encrypt_secret.call_args
        aad = call_args[1]['aad']

        self.assertIs(aad['organization_id'], self.organization_id)
        self.assertIs(aad['user_id'], self.user_id)
        self.assertIs(aad['datastore_id'], self.datastore_id)

    def test_encrypt_secret_crypto_client_exception_propagates(self):
        self.mock_crypto_client.encrypt_secret.side_effect = Exception('Encryption failed')

        with self.assertRaises(Exception) as context:
            encrypt_secret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                plaintext=self.plaintext,
                crypto_client=self.mock_crypto_client
            )

        self.assertEqual(str(context.exception), 'Encryption failed')

    def test_encrypt_secret_with_whitespace_plaintext(self):
        whitespace_plaintext = '   \t\n  '

        _ = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=whitespace_plaintext,
            crypto_client=self.mock_crypto_client
        )

        call_args = self.mock_crypto_client.encrypt_secret.call_args
        self.assertEqual(call_args[1]['plaintext'], whitespace_plaintext)

    def test_encrypt_secret_returns_datastore_secret_instance(self):
        result = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=self.plaintext,
            crypto_client=self.mock_crypto_client
        )

        self.assertIsInstance(result, DataStoreSecret)

    def test_encrypt_secret_different_uuids_for_different_entities(self):
        org_id_1 = uuid4()
        org_id_2 = uuid4()
        user_id_1 = uuid4()
        datastore_id_1 = uuid4()

        self.assertNotEqual(org_id_1, org_id_2)
        self.assertNotEqual(org_id_1, user_id_1)
        self.assertNotEqual(user_id_1, datastore_id_1)

        result = encrypt_secret(
            organization_id=org_id_1,
            user_id=user_id_1,
            datastore_id=datastore_id_1,
            plaintext=self.plaintext,
            crypto_client=self.mock_crypto_client
        )

        self.assertEqual(result.organization_id, org_id_1)
        self.assertEqual(result.user_id, user_id_1)
        self.assertEqual(result.datastore_id, datastore_id_1)

    def test_encrypt_secret_with_multiple_kwargs(self):
        kwargs = {
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-02T00:00:00Z',
            'version': 2,
            'is_active': True,
            'metadata': {'key': 'value'}
        }

        with patch('integration_service.services.encryption.encrypt_secret.DataStoreSecret') as mock_secret_class:
            mock_secret_instance = Mock()
            mock_secret_class.return_value = mock_secret_instance

            _ = encrypt_secret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                plaintext=self.plaintext,
                crypto_client=self.mock_crypto_client,
                **kwargs
            )

            call_kwargs = mock_secret_class.call_args[1]
            self.assertEqual(call_kwargs['created_at'], '2025-01-01T00:00:00Z')
            self.assertEqual(call_kwargs['updated_at'], '2025-01-02T00:00:00Z')
            self.assertEqual(call_kwargs['version'], 2)
            self.assertTrue(call_kwargs['is_active'])
            self.assertEqual(call_kwargs['metadata'], {'key': 'value'})

    def test_encrypt_secret_without_kwargs(self):
        with patch('integration_service.services.encryption.encrypt_secret.DataStoreSecret') as mock_secret_class:
            mock_secret_instance = Mock()
            mock_secret_class.return_value = mock_secret_instance

            _ = encrypt_secret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                plaintext=self.plaintext,
                crypto_client=self.mock_crypto_client
            )

            call_kwargs = mock_secret_class.call_args[1]
            required_keys = {
                'organization_id', 'user_id', 'datastore_id',
                'ciphertext', 'nonce', 'tag', 'wrapped_dek'
            }
            self.assertEqual(set(call_kwargs.keys()), required_keys)

    def test_encrypt_secret_encrypted_result_fields_passed_correctly(self):
        custom_ciphertext = b'custom_encrypted_data_123'
        custom_nonce = b'custom_nonce_456'
        custom_tag = b'custom_tag_789'
        custom_wrapped_dek = b'custom_wrapped_key_012'

        self.mock_encrypted_result.ciphertext = custom_ciphertext
        self.mock_encrypted_result.nonce = custom_nonce
        self.mock_encrypted_result.tag = custom_tag
        self.mock_encrypted_result.wrapped_dek = custom_wrapped_dek

        result = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=self.plaintext,
            crypto_client=self.mock_crypto_client
        )

        self.assertEqual(result.ciphertext, custom_ciphertext)
        self.assertEqual(result.nonce, custom_nonce)
        self.assertEqual(result.tag, custom_tag)
        self.assertEqual(result.wrapped_dek, custom_wrapped_dek)

    def test_encrypt_secret_calls_crypto_client_exactly_once(self):
        encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=self.plaintext,
            crypto_client=self.mock_crypto_client
        )

        self.assertEqual(self.mock_crypto_client.encrypt_secret.call_count, 1)

    def test_encrypt_secret_with_newlines_and_tabs(self):
        plaintext_with_formatting = 'line1\nline2\tcolumn1\tcolumn2\r\nline3'

        _ = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=plaintext_with_formatting,
            crypto_client=self.mock_crypto_client
        )

        call_args = self.mock_crypto_client.encrypt_secret.call_args
        self.assertEqual(call_args[1]['plaintext'], plaintext_with_formatting)

    def test_encrypt_secret_json_string(self):
        json_plaintext = "{'api_key': 'secret123', 'token': 'xyz789'}"

        _ = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=json_plaintext,
            crypto_client=self.mock_crypto_client
        )

        call_args = self.mock_crypto_client.encrypt_secret.call_args
        self.assertEqual(call_args[1]['plaintext'], json_plaintext)


class TestEncryptSecretDataStore(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.datastore_id = uuid4()
        self.mock_crypto_client = Mock(spec=CryptoClient)

    def test_encrypt_secret_end_to_end_flow(self):
        plaintext = 'my_secret_api_key_12345'

        mock_encrypted_result = Mock()
        mock_encrypted_result.ciphertext = b'\x00\x01\x02\x03'
        mock_encrypted_result.nonce = b'\x04\x05\x06'
        mock_encrypted_result.tag = b'\x07\x08'
        mock_encrypted_result.wrapped_dek = b'\x09\x0a\x0b'

        self.mock_crypto_client.encrypt_secret.return_value = mock_encrypted_result

        result = encrypt_secret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            plaintext=plaintext,
            crypto_client=self.mock_crypto_client
        )

        self.assertIsInstance(result, DataStoreSecret)
        self.assertEqual(result.organization_id, self.organization_id)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.datastore_id, self.datastore_id)
        self.assertEqual(result.ciphertext, b'\x00\x01\x02\x03')
        self.assertEqual(result.nonce, b'\x04\x05\x06')
        self.assertEqual(result.tag, b'\x07\x08')
        self.assertEqual(result.wrapped_dek, b'\x09\x0a\x0b')

        self.mock_crypto_client.encrypt_secret.assert_called_once_with(
            plaintext=plaintext,
            aad={
                'organization_id': self.organization_id,
                'user_id': self.user_id,
                'datastore_id': self.datastore_id
            }
        )



def make_encrypted_secret() -> EncryptedSecret:
    return MagicMock(spec=EncryptedSecret)


class TestEncryptConnParams(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.api_base = 'https://router.huggingface.co/v1'
        self.model_id = 'openai/meta-llama/Llama-3.1-8B-Instruct'
        self.conn_params = {'api_key': 'hf-test-key', 'extra_param': 'value'}
        self.mock_crypto_client = MagicMock(spec=CryptoClient)
        self.mock_crypto_client.encrypt_secret.return_value = make_encrypted_secret()

    def _call(self, **overrides):
        defaults = {
            'organization_id': self.organization_id,
            'user_id': self.user_id,
            'api_base': self.api_base,
            'model_id': self.model_id,
            'crypto_client': self.mock_crypto_client,
            'conn_params': self.conn_params,
        }
        return encrypt_conn_params(**{**defaults, **overrides})

    def test_returns_encrypted_secret(self):
        result = self._call()
        self.assertIsInstance(result, MagicMock)
        self.assertIs(result, self.mock_crypto_client.encrypt_secret.return_value)

    def test_calls_encrypt_secret_once(self):
        self._call()
        self.mock_crypto_client.encrypt_secret.assert_called_once()

    def test_serializes_conn_params_as_json(self):
        self._call()
        call_kwargs = self.mock_crypto_client.encrypt_secret.call_args.kwargs
        self.assertEqual(call_kwargs['plaintext'], json.dumps(self.conn_params))

    def test_passes_organization_id_in_aad(self):
        self._call()
        aad = self.mock_crypto_client.encrypt_secret.call_args.kwargs['aad']
        self.assertEqual(aad['organization_id'], self.organization_id)

    def test_passes_user_id_in_aad(self):
        self._call()
        aad = self.mock_crypto_client.encrypt_secret.call_args.kwargs['aad']
        self.assertEqual(aad['user_id'], self.user_id)

    def test_passes_api_base_in_aad(self):
        self._call()
        aad = self.mock_crypto_client.encrypt_secret.call_args.kwargs['aad']
        self.assertEqual(aad['api_base'], self.api_base)

    def test_passes_model_id_in_aad(self):
        self._call()
        aad = self.mock_crypto_client.encrypt_secret.call_args.kwargs['aad']
        self.assertEqual(aad['model_id'], self.model_id)

    def test_aad_contains_exactly_four_keys(self):
        self._call()
        aad = self.mock_crypto_client.encrypt_secret.call_args.kwargs['aad']
        self.assertSetEqual(
            set(aad.keys()),
            {'organization_id', 'user_id', 'api_base', 'model_id'}
        )

    def test_empty_conn_params_serialized_as_empty_json_object(self):
        self._call(conn_params={})
        call_kwargs = self.mock_crypto_client.encrypt_secret.call_args.kwargs
        self.assertEqual(call_kwargs['plaintext'], json.dumps({}))

    def test_nested_conn_params_serialized_correctly(self):
        nested = {'api_key': 'key', 'nested': {'a': 1, 'b': 2}}
        self._call(conn_params=nested)
        call_kwargs = self.mock_crypto_client.encrypt_secret.call_args.kwargs
        self.assertEqual(call_kwargs['plaintext'], json.dumps(nested))

    def test_different_org_ids_produce_different_aad(self):
        org_1 = uuid4()
        org_2 = uuid4()

        self._call(organization_id=org_1)
        aad_1 = self.mock_crypto_client.encrypt_secret.call_args.kwargs['aad']

        self.mock_crypto_client.reset_mock()

        self._call(organization_id=org_2)
        aad_2 = self.mock_crypto_client.encrypt_secret.call_args.kwargs['aad']

        self.assertNotEqual(aad_1['organization_id'], aad_2['organization_id'])

    def test_crypto_client_error_propagates(self):
        self.mock_crypto_client.encrypt_secret.side_effect = RuntimeError('vault unreachable')

        with self.assertRaises(RuntimeError):
            self._call()

