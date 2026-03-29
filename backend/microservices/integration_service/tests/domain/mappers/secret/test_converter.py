import unittest
from unittest.mock import Mock, patch
from uuid import uuid4, UUID
from pydantic import SecretStr, BaseModel, Field

from svc_integration_contracts.models import (
    DataStoreUpdateRequest,
    DataStoreCreateRequest,
    Auth,
    DB,
    Cloud
)

from integration_service.database.models import SecretORM
from integration_service.domain.models.secret import DataStoreSecret
from integration_service.domain.mappers.secret import (
    secrets_from_dto,
    secrets_from_orm,
    orm_from_secrets
)
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient


class MockDataStoreUpdateRequest(BaseModel):
    connection_name: str | None = Field(..., title="Connection Name")
    host: str | None = Field(..., title="Host")
    port: int | None = Field(..., title="Port")
    database_name: str | None = Field(..., title="Database Name")
    autosync_on: bool | None = Field(..., title="Autosync On")
    password: SecretStr | None = Field(..., title="Password")

class TestSecretsFromDTO(unittest.TestCase):
    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.datastore_id = uuid4()
        self.mock_crypto_client = Mock(spec=CryptoClient)

        self.mock_encrypted_secret = DataStoreSecret(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            ciphertext=b'encrypted_data',
            nonce=b'nonce_12345',
            tag=b'tag_67890',
            wrapped_dek=b'wrapped_key',
            enc_alg='AES-256-GCM',
            wrap_alg='RSA-OAEP',
            encoding='base64',
        )

    @patch('integration_service.domain.mappers.secret.converter.encrypt_secret')
    def test_extracts_secret_fields_from_update_request(self, mock_encrypt):
        mock_encrypt.return_value = self.mock_encrypted_secret

        payload = MockDataStoreUpdateRequest(
            connection_name='test',
            host='localhost',
            port=5432,
            database_name='test_db',
            autosync_on=True,
            password=SecretStr('secret')
        )

        result = secrets_from_dto(
            self.organization_id,
            self.user_id,
            self.datastore_id,
            self.mock_crypto_client,
            payload
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)
        self.assertIn('password', result)

        self.assertEqual(mock_encrypt.call_count, 1)

        first_call = mock_encrypt.call_args_list[0]
        self.assertEqual(first_call[1]['organization_id'], self.organization_id)
        self.assertEqual(first_call[1]['user_id'], self.user_id)
        self.assertEqual(first_call[1]['datastore_id'], self.datastore_id)
        self.assertEqual(first_call[1]['plaintext'], 'secret')
        self.assertEqual(first_call[1]['crypto_client'], self.mock_crypto_client)

    @patch('integration_service.domain.mappers.secret.converter.encrypt_secret')
    def test_extracts_secret_fields_from_create_request(self, mock_encrypt):
        mock_encrypt.return_value = self.mock_encrypted_secret

        tenant_id = 'tenant_id'
        client_id = 'client_id'
        kek_kid = 'kek_id'

        payload = DataStoreCreateRequest(
            auth=Auth.password_native,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name='test',
            descr='test-descr',
            host='localhost',
            database_name='test_db',
            kek_kid=kek_kid,
            port=5432,
            warehouse='warehouse1',
            tenant_id=tenant_id,
            client_id=client_id,
            region='us-east-1',
            azure_cert_kid=None,
            azure_cert_name=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=True,
            username=SecretStr('admin_user'),
            password=SecretStr('super_secret_pass'),
            client_secret=SecretStr('oauth_client_secret')
        )

        result = secrets_from_dto(
            self.organization_id,
            self.user_id,
            self.datastore_id,
            self.mock_crypto_client,
            payload
        )

        self.assertEqual(len(result), 3)
        self.assertIn('username', result)
        self.assertIn('password', result)
        self.assertEqual(mock_encrypt.call_count, 3)

    @patch('integration_service.domain.mappers.secret.converter.encrypt_secret')
    def test_ignores_non_secret_fields(self, mock_encrypt):
        mock_encrypt.return_value = self.mock_encrypted_secret

        tenant_id = 'tenant_id'
        client_id = 'client_id'
        kek_kid = 'kek_id'

        payload = DataStoreCreateRequest(
            auth=Auth.password_native,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name='test',
            descr='test-descr',
            host='localhost',
            database_name='test_db',
            kek_kid=kek_kid,
            port=5432,
            warehouse='warehouse1',
            tenant_id=tenant_id,
            client_id=client_id,
            region='us-east-1',
            azure_cert_kid=None,
            azure_cert_name=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=True,
            username=SecretStr('admin_user'),
            password=SecretStr('super_secret_pass'),
            client_secret=SecretStr('oauth_client_secret')
        )

        result = secrets_from_dto(
            self.organization_id,
            self.user_id,
            self.datastore_id,
            self.mock_crypto_client,
            payload
        )

        self.assertEqual(len(result), 3)
        self.assertIn('password', result)
        mock_encrypt.assert_called()

    @patch('integration_service.domain.mappers.secret.converter.encrypt_secret')
    def test_handles_payload_with_no_secrets(self, mock_encrypt):
        payload = DataStoreUpdateRequest(
            connection_name='test',
            host='localhost',
            port=5432,
            database_name='test_db',
            autosync_on=True
        )

        result = secrets_from_dto(
            self.organization_id,
            self.user_id,
            self.datastore_id,
            self.mock_crypto_client,
            payload
        )

        self.assertEqual(len(result), 0)
        self.assertEqual(result, {})
        mock_encrypt.assert_not_called()

    @patch('integration_service.domain.mappers.secret.converter.encrypt_secret')
    def test_passes_kwargs_to_encrypt_secret(self, mock_encrypt):
        mock_encrypt.return_value = self.mock_encrypted_secret

        tenant_id = 'tenant_id'
        client_id = 'client_id'
        kek_kid = 'kek_id'

        payload = DataStoreCreateRequest(
            auth=Auth.password_native,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name='test',
            descr='test-descr',
            host='localhost',
            database_name='test_db',
            kek_kid=kek_kid,
            port=5432,
            warehouse='warehouse1',
            tenant_id=tenant_id,
            client_id=client_id,
            region='us-east-1',
            azure_cert_kid=None,
            azure_cert_name=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=True,
            username=SecretStr('admin_user'),
            password=SecretStr('super_secret_pass'),
            client_secret=SecretStr('oauth_client_secret')
        )

        extra_kwarg1 = 'value1'
        extra_kwarg2 = 42

        result = secrets_from_dto(
            self.organization_id,
            self.user_id,
            self.datastore_id,
            self.mock_crypto_client,
            payload,
            extra_kwarg1=extra_kwarg1,
            extra_kwarg2=extra_kwarg2
        )

        mock_encrypt.assert_called()
        call_kwargs = mock_encrypt.call_args[1]
        self.assertEqual(call_kwargs['extra_kwarg1'], extra_kwarg1)
        self.assertEqual(call_kwargs['extra_kwarg2'], extra_kwarg2)

    @patch('integration_service.domain.mappers.secret.converter.encrypt_secret')
    def test_returns_dict_with_correct_secret_types(self, mock_encrypt):
        mock_encrypt.return_value = self.mock_encrypted_secret

        payload = DataStoreUpdateRequest(
            connection_name='test',
            host='localhost',
            port=5432,
            database_name='test_db',
            autosync_on=True,
            password=SecretStr('pwd'),
            api_key=SecretStr('key')
        )

        result = secrets_from_dto(
            self.organization_id,
            self.user_id,
            self.datastore_id,
            self.mock_crypto_client,
            payload
        )

        for key, value in result.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, DataStoreSecret)
            self.assertEqual(value.organization_id, self.organization_id)
            self.assertEqual(value.user_id, self.user_id)
            self.assertEqual(value.datastore_id, self.datastore_id)


class TestSecretsFromORM(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.datastore_id = uuid4()

    def test_converts_single_secret_orm_to_domain(self):
        secret_orm = SecretORM(
            id=uuid4(),
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            secret_type='password',
            ciphertext=b'encrypted_password',
            nonce=b'nonce_abc',
            tag=b'tag_xyz',
            wrapped_dek=b'wrapped_key',
            enc_alg='AES-256-GCM',
            wrap_alg='RSA-OAEP',
            encoding='base64',
        )

        result = secrets_from_orm([secret_orm])

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)
        self.assertIn('password', result)

        secret = result['password']
        self.assertIsInstance(secret, DataStoreSecret)
        self.assertEqual(secret.organization_id, self.organization_id)
        self.assertEqual(secret.user_id, self.user_id)
        self.assertEqual(secret.datastore_id, self.datastore_id)
        self.assertEqual(secret.ciphertext, b'encrypted_password')
        self.assertEqual(secret.nonce, b'nonce_abc')
        self.assertEqual(secret.tag, b'tag_xyz')
        self.assertEqual(secret.wrapped_dek, b'wrapped_key')
        self.assertEqual(secret.enc_alg, 'AES-256-GCM')
        self.assertEqual(secret.wrap_alg, 'RSA-OAEP')
        self.assertEqual(secret.encoding, 'base64')

    def test_converts_multiple_secret_orms(self):
        secrets_orm = [
            SecretORM(
                id=uuid4(),
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                secret_type='password',
                ciphertext=b'enc_password',
                nonce=b'nonce1',
                tag=b'tag1',
                wrapped_dek=b'key1',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
            ),
            SecretORM(
                id=uuid4(),
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                secret_type='api_key',
                ciphertext=b'enc_api_key',
                nonce=b'nonce2',
                tag=b'tag2',
                wrapped_dek=b'key2',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
            ),
            SecretORM(
                id=uuid4(),
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                secret_type='client_secret',
                ciphertext=b'enc_client_secret',
                nonce=b'nonce3',
                tag=b'tag3',
                wrapped_dek=b'key3',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
            )
        ]

        result = secrets_from_orm(secrets_orm)

        self.assertEqual(len(result), 3)
        self.assertIn('password', result)
        self.assertIn('api_key', result)
        self.assertIn('client_secret', result)

        for secret_type, secret in result.items():
            self.assertIsInstance(secret, DataStoreSecret)
            self.assertEqual(secret.organization_id, self.organization_id)

    def test_handles_empty_list(self):
        result = secrets_from_orm([])

        self.assertEqual(result, {})
        self.assertEqual(len(result), 0)

    def test_preserves_uuid_types(self):
        secret_orm = SecretORM(
            id=uuid4(),
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
            secret_type='password',
            ciphertext=b'encrypted',
            nonce=b'nonce',
            tag=b'tag',
            wrapped_dek=b'key',
            enc_alg='AES-256-GCM',
            wrap_alg='RSA-OAEP',
            encoding='base64',
        )

        result = secrets_from_orm([secret_orm])

        secret = result['password']
        self.assertIsInstance(secret.organization_id, UUID)
        self.assertIsInstance(secret.user_id, UUID)
        self.assertIsInstance(secret.datastore_id, UUID)


class TestORMFromSecrets(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.datastore_id = uuid4()

    def test_converts_single_secret_to_orm(self):
        secrets = {
            'password': DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                ciphertext=b'encrypted_password',
                nonce=b'nonce_abc',
                tag=b'tag_xyz',
                wrapped_dek=b'wrapped_key',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
            )
        }

        result = orm_from_secrets(secrets)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        secret_orm = result[0]
        self.assertIsInstance(secret_orm, SecretORM)
        self.assertEqual(secret_orm.organization_id, self.organization_id)
        self.assertEqual(secret_orm.user_id, self.user_id)
        self.assertEqual(secret_orm.datastore_id, self.datastore_id)
        self.assertEqual(secret_orm.secret_type, 'password')
        self.assertEqual(secret_orm.ciphertext, b'encrypted_password')
        self.assertEqual(secret_orm.nonce, b'nonce_abc')
        self.assertEqual(secret_orm.tag, b'tag_xyz')
        self.assertEqual(secret_orm.wrapped_dek, b'wrapped_key')
        self.assertEqual(secret_orm.enc_alg, 'AES-256-GCM')
        self.assertEqual(secret_orm.wrap_alg, 'RSA-OAEP')
        self.assertEqual(secret_orm.encoding, 'base64')

    def test_converts_multiple_secrets_to_orm(self):
        secrets = {
            'password': DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                ciphertext=b'enc_pwd',
                nonce=b'nonce1',
                tag=b'tag1',
                wrapped_dek=b'key1',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
            ),
            'api_key': DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                ciphertext=b'enc_key',
                nonce=b'nonce2',
                tag=b'tag2',
                wrapped_dek=b'key2',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
            ),
            'client_secret': DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                ciphertext=b'enc_client',
                nonce=b'nonce3',
                tag=b'tag3',
                wrapped_dek=b'key3',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
            )
        }

        result = orm_from_secrets(secrets)

        self.assertEqual(len(result), 3)

        secret_types = {orm.secret_type for orm in result}
        self.assertEqual(secret_types, {'password', 'api_key', 'client_secret'})

        for secret_orm in result:
            self.assertIsInstance(secret_orm, SecretORM)
            self.assertEqual(secret_orm.organization_id, self.organization_id)
            self.assertEqual(secret_orm.user_id, self.user_id)
            self.assertEqual(secret_orm.datastore_id, self.datastore_id)

    def test_handles_empty_dict(self):
        result = orm_from_secrets({})

        self.assertEqual(result, [])
        self.assertEqual(len(result), 0)


class TestSecretConversionRoundTrip(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.datastore_id = uuid4()

    def test_domain_to_orm_to_domain_round_trip(self):
        original_secrets = {
            'password': DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                ciphertext=b'encrypted_password',
                nonce=b'nonce_abc123',
                tag=b'tag_xyz789',
                wrapped_dek=b'wrapped_key_data',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
            ),
            'api_key': DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                ciphertext=b'encrypted_api_key',
                nonce=b'nonce_def456',
                tag=b'tag_uvw012',
                wrapped_dek=b'wrapped_api_key',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
            )
        }

        orm_list = orm_from_secrets(original_secrets)

        result_secrets = secrets_from_orm(orm_list)

        self.assertEqual(len(result_secrets), len(original_secrets))

        for secret_type, original in original_secrets.items():
            result = result_secrets[secret_type]

            self.assertEqual(result.organization_id, original.organization_id)
            self.assertEqual(result.user_id, original.user_id)
            self.assertEqual(result.datastore_id, original.datastore_id)
            self.assertEqual(result.ciphertext, original.ciphertext)
            self.assertEqual(result.nonce, original.nonce)
            self.assertEqual(result.tag, original.tag)
            self.assertEqual(result.wrapped_dek, original.wrapped_dek)
            self.assertEqual(result.enc_alg, original.enc_alg)
            self.assertEqual(result.wrap_alg, original.wrap_alg)
            self.assertEqual(result.encoding, original.encoding)