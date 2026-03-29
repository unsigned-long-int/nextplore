import unittest
from unittest.mock import patch, MagicMock

from uuid import uuid4

from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from nextplore_sdk.encryptor.client.encrypted_secret import EncryptedSecret

from integration_service.database.models import UserLlmORM
from integration_service.domain.models.user_llm import UserLlm
from integration_service.domain.mappers.user_llm.converter import (
    orm_from_user_llm,
    user_llm_from_orm,
    user_llm_from_dto,
    user_llm_profile_from_orm
)
from svc_integration_contracts.models import UserLlmCreateRequest




MODULE = 'integration_service.domain.mappers.user_llm.converter'


def make_encrypted_secret(**overrides) -> EncryptedSecret:
    mock = MagicMock(spec=EncryptedSecret)
    mock.ciphertext = overrides.get('ciphertext', b'ciphertext')
    mock.nonce = overrides.get('nonce', b'nonce')
    mock.tag = overrides.get('tag', b'tag')
    mock.wrapped_dek = overrides.get('wrapped_dek', b'wrapped_dek')
    return mock


def make_user_llm(**overrides) -> UserLlm:
    defaults = {
        'model_id': 'openai/meta-llama/Llama-3.1-8B-Instruct',
        'label': 'My Llama endpoint',
        'api_base': 'https://router.huggingface.co/v1',
        'nonce': b'nonce',
        'encrypted_conn_params': make_encrypted_secret(),
        'max_tokens': 4096,
    }
    return UserLlm(**{**defaults, **overrides})


def make_orm(**overrides) -> UserLlmORM:
    defaults = {
        'model_id': 'openai/meta-llama/Llama-3.1-8B-Instruct',
        'label': 'My Llama endpoint',
        'api_base': 'https://router.huggingface.co/v1',
        'max_tokens': 4096,
        'encrypted_connection_params': b'ciphertext',
        'nonce': b'nonce',
        'tag': b'tag',
        'wrapped_dek': b'wrapped_dek',
    }
    return UserLlmORM(**{**defaults, **overrides})


def make_payload(**overrides) -> UserLlmCreateRequest:
    defaults = {
        'model_id': 'openai/meta-llama/Llama-3.1-8B-Instruct',
        'label': 'My Llama endpoint',
        'api_base': 'https://router.huggingface.co/v1',
        'connection_params': {'api_key': 'hf-test-key'},
        'max_tokens': 4096,
        'kek_kid': 'https://vault.azure.net/keys/test-key/version',
    }
    return UserLlmCreateRequest(**{**defaults, **overrides})


class TestOrmFromUserHostedModel(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.llm = make_user_llm()

    def _call(self, **overrides) -> UserLlmORM:
        return orm_from_user_llm(
            organization_id=overrides.get('organization_id', self.organization_id),
            user_id=overrides.get('user_id', self.user_id),
            user_llm=overrides.get('user_llm', self.llm),
        )

    def test_returns_orm_instance(self):
        result = self._call()
        self.assertIsInstance(result, UserLlmORM)

    def test_maps_organization_id(self):
        result = self._call()
        self.assertEqual(result.organization_id, self.organization_id)

    def test_maps_user_id(self):
        result = self._call()
        self.assertEqual(result.user_id, self.user_id)

    def test_maps_model_id(self):
        result = self._call()
        self.assertEqual(result.model_id, self.llm.model_id)

    def test_maps_label(self):
        result = self._call()
        self.assertEqual(result.label, self.llm.label)

    def test_maps_api_base(self):
        result = self._call()
        self.assertEqual(result.api_base, self.llm.api_base)

    def test_maps_max_tokens(self):
        result = self._call()
        self.assertEqual(result.max_tokens, self.llm.max_tokens)

    def test_maps_ciphertext(self):
        result = self._call()
        self.assertEqual(result.encrypted_connection_params, self.llm.encrypted_conn_params.ciphertext)

    def test_maps_nonce(self):
        result = self._call()
        self.assertEqual(result.nonce, self.llm.encrypted_conn_params.nonce)

    def test_maps_tag(self):
        result = self._call()
        self.assertEqual(result.tag, self.llm.encrypted_conn_params.tag)

    def test_maps_wrapped_dek(self):
        result = self._call()
        self.assertEqual(result.wrapped_dek, self.llm.encrypted_conn_params.wrapped_dek)


class TestUserLlmFromOrm(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.orm = make_orm()

    def _call(self, **overrides) -> UserLlm:
        return user_llm_from_orm(
            organization_id=overrides.get('organization_id', self.organization_id),
            user_id=overrides.get('user_id', self.user_id),
            user_llm_orm=overrides.get('user_llm_orm', self.orm),
        )

    def test_returns_user_llm(self):
        result = self._call()
        self.assertIsInstance(result, UserLlm)

    def test_maps_model_id(self):
        result = self._call()
        self.assertEqual(result.model_id, self.orm.model_id)

    def test_maps_label(self):
        result = self._call()
        self.assertEqual(result.label, self.orm.label)

    def test_maps_api_base(self):
        result = self._call()
        self.assertEqual(result.api_base, self.orm.api_base)

    def test_maps_max_tokens(self):
        result = self._call()
        self.assertEqual(result.max_tokens, self.orm.max_tokens)

    def test_maps_nonce(self):
        result = self._call()
        self.assertEqual(result.nonce, self.orm.nonce)

    def test_builds_encrypted_secret_with_nonce(self):
        result = self._call()
        self.assertEqual(result.encrypted_conn_params.nonce, self.orm.nonce)

    def test_builds_encrypted_secret_with_tag(self):
        result = self._call()
        self.assertEqual(result.encrypted_conn_params.tag, self.orm.tag)

    def test_builds_encrypted_secret_with_ciphertext(self):
        result = self._call()
        self.assertEqual(result.encrypted_conn_params.ciphertext, self.orm.encrypted_connection_params)

    def test_builds_encrypted_secret_with_wrapped_dek(self):
        result = self._call()
        self.assertEqual(result.encrypted_conn_params.wrapped_dek, self.orm.wrapped_dek)

    def test_aad_contains_organization_id(self):
        result = self._call()
        self.assertEqual(result.encrypted_conn_params.aad['organization_id'], self.organization_id)

    def test_aad_contains_user_id(self):
        result = self._call()
        self.assertEqual(result.encrypted_conn_params.aad['user_id'], self.user_id)

    def test_aad_contains_api_base(self):
        result = self._call()
        self.assertEqual(result.encrypted_conn_params.aad['api_base'], self.orm.api_base)

    def test_aad_contains_model_id(self):
        result = self._call()
        self.assertEqual(result.encrypted_conn_params.aad['model_id'], self.orm.model_id)

    def test_aad_has_exactly_four_keys(self):
        result = self._call()
        self.assertSetEqual(
            set(result.encrypted_conn_params.aad.keys()),
            {'organization_id', 'user_id', 'api_base', 'model_id'}
        )


class TestUserLlmFromDto(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.payload = make_payload()
        self.mock_crypto_client = MagicMock(spec=CryptoClient)
        self.mock_encrypted_secret = make_encrypted_secret()

    def _call(self, **overrides) -> UserLlm:
        with patch(f'{MODULE}.encrypt_conn_params', return_value=self.mock_encrypted_secret) as self.mock_encrypt:
            return user_llm_from_dto(
                organization_id=overrides.get('organization_id', self.organization_id),
                user_id=overrides.get('user_id', self.user_id),
                payload=overrides.get('payload', self.payload),
                crypto_client=overrides.get('crypto_client', self.mock_crypto_client),
            )

    def test_returns_user_llm(self):
        result = self._call()
        self.assertIsInstance(result, UserLlm)

    def test_maps_model_id(self):
        result = self._call()
        self.assertEqual(result.model_id, self.payload.model_id)

    def test_maps_label(self):
        result = self._call()
        self.assertEqual(result.label, self.payload.label)

    def test_maps_api_base(self):
        result = self._call()
        self.assertEqual(result.api_base, self.payload.api_base)

    def test_maps_max_tokens(self):
        result = self._call()
        self.assertEqual(result.max_tokens, self.payload.max_tokens)

    def test_maps_nonce_from_encrypted_secret(self):
        result = self._call()
        self.assertEqual(result.nonce, self.mock_encrypted_secret.nonce)

    def test_sets_encrypted_conn_params(self):
        result = self._call()
        self.assertIs(result.encrypted_conn_params, self.mock_encrypted_secret)

    def test_calls_encrypt_conn_params_with_correct_args(self):
        with patch(f'{MODULE}.encrypt_conn_params', return_value=self.mock_encrypted_secret) as mock_encrypt:
            user_llm_from_dto(
                organization_id=self.organization_id,
                user_id=self.user_id,
                payload=self.payload,
                crypto_client=self.mock_crypto_client,
            )
            mock_encrypt.assert_called_once_with(
                organization_id=self.organization_id,
                user_id=self.user_id,
                model_id=self.payload.model_id,
                api_base=self.payload.api_base,
                crypto_client=self.mock_crypto_client,
                conn_params=self.payload.connection_params,
            )

    def test_encrypt_error_propagates(self):
        with patch(f'{MODULE}.encrypt_conn_params', side_effect=RuntimeError('vault down')):
            with self.assertRaises(RuntimeError):
                user_llm_from_dto(
                    organization_id=self.organization_id,
                    user_id=self.user_id,
                    payload=self.payload,
                    crypto_client=self.mock_crypto_client,
                )




def make_user_llm_orm(**overrides):
    orm = MagicMock()
    orm.api_base = 'https://api.openai.com/v1'
    orm.model_id = 'gpt-4o'
    orm.label = 'GPT-4o'
    orm.max_tokens = 4096
    for k, v in overrides.items():
        setattr(orm, k, v)
    return orm


class TestUserLlmProfileFromOrm(unittest.TestCase):

    def test_maps_api_base(self):
        result = user_llm_profile_from_orm(make_user_llm_orm())
        self.assertEqual(result.api_base, 'https://api.openai.com/v1')

    def test_maps_model_id(self):
        result = user_llm_profile_from_orm(make_user_llm_orm())
        self.assertEqual(result.model_id, 'gpt-4o')

    def test_maps_label(self):
        result = user_llm_profile_from_orm(make_user_llm_orm())
        self.assertEqual(result.label, 'GPT-4o')

    def test_maps_max_tokens(self):
        result = user_llm_profile_from_orm(make_user_llm_orm())
        self.assertEqual(result.max_tokens, 4096)

    def test_returns_user_llm_profile_instance(self):
        from integration_service.domain.models.user_llm import UserLlmProfile
        result = user_llm_profile_from_orm(make_user_llm_orm())
        self.assertIsInstance(result, UserLlmProfile)

    def test_maps_custom_api_base(self):
        result = user_llm_profile_from_orm(make_user_llm_orm(api_base='https://custom.endpoint.com/v1'))
        self.assertEqual(result.api_base, 'https://custom.endpoint.com/v1')

    def test_maps_custom_model_id(self):
        result = user_llm_profile_from_orm(make_user_llm_orm(model_id='claude-3-5-sonnet'))
        self.assertEqual(result.model_id, 'claude-3-5-sonnet')

    def test_maps_custom_max_tokens(self):
        result = user_llm_profile_from_orm(make_user_llm_orm(max_tokens=8192))
        self.assertEqual(result.max_tokens, 8192)

    def test_does_not_expose_orm_fields(self):
        result = user_llm_profile_from_orm(make_user_llm_orm())
        self.assertFalse(hasattr(result, 'connection_params'))
        self.assertFalse(hasattr(result, 'encrypted_api_key'))