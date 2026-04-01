import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from integration_service.api.context import UserIdentity
from integration_service.database.exceptions import UserLlmGetFailed
from integration_service.database.repositories import LlmRepository
from integration_service.services.llm import LlmService
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from svc_integration_contracts.models import UserLlmConfig


MODULE = 'integration_service.services.llm.llm_service'


def make_user_identity(**overrides) -> UserIdentity:
    defaults = {
        'organization_id': uuid4(),
        'user_id': uuid4(),
    }
    return UserIdentity(**{**defaults, **overrides})


def make_user_llm_mock(
    api_base='https://api.openai.com/v1',
    max_tokens=4096,
    kek_kid='https://vault.azure.net/keys/test-key/version',
):
    mock = MagicMock()
    mock.api_base = api_base
    mock.max_tokens = max_tokens
    mock.kek_kid = kek_kid
    mock.reveal.return_value = {'api_key': 'decrypted-key'}
    return mock


class TestLlmServiceGetConfig(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_repo = AsyncMock(spec=LlmRepository)
        self.mock_cache_service = AsyncMock()
        self.mock_crypto_client = MagicMock(spec=CryptoClient)
        self.mock_crypto_client_factory = MagicMock(return_value=self.mock_crypto_client)

        self.service = LlmService(
            repo=self.mock_repo,
            cache_service=self.mock_cache_service,
            crypto_client_factory=self.mock_crypto_client_factory,
        )

        self.user_identity = make_user_identity()
        self.organization_id = self.user_identity.organization_id
        self.user_id = self.user_identity.user_id
        self.model_id = uuid4()

        self.mock_user_llm = make_user_llm_mock()
        self.mock_config = MagicMock(spec=UserLlmConfig)


    async def test_returns_cached_config_when_cache_hit(self):
        self.mock_cache_service.get_user_llm_config.return_value = self.mock_config

        result = await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.assertEqual(result, self.mock_config)

    async def test_does_not_call_repo_when_cache_hit(self):
        self.mock_cache_service.get_user_llm_config.return_value = self.mock_config

        await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.mock_repo.get_user_llm.assert_not_awaited()

    async def test_does_not_call_crypto_factory_when_cache_hit(self):
        self.mock_cache_service.get_user_llm_config.return_value = self.mock_config

        await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.mock_crypto_client_factory.assert_not_called()

    async def test_does_not_set_cache_when_cache_hit(self):
        self.mock_cache_service.get_user_llm_config.return_value = self.mock_config

        await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.mock_cache_service.set_user_llm_config.assert_not_awaited()

    async def test_calls_cache_get_with_correct_args(self):
        self.mock_cache_service.get_user_llm_config.return_value = self.mock_config

        await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.mock_cache_service.get_user_llm_config.assert_awaited_once_with(
            user_identity=self.user_identity,
            model_ref_id=self.model_id,
        )


    async def test_calls_repo_when_cache_miss(self):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.return_value = self.mock_user_llm

        await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.mock_repo.get_user_llm.assert_awaited_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            model_ref_id=self.model_id,
        )

    async def test_calls_crypto_factory_with_kek_kid_on_cache_miss(self):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.return_value = self.mock_user_llm

        await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.mock_crypto_client_factory.assert_called_once_with(self.mock_user_llm.kek_kid)

    async def test_calls_reveal_with_correct_args(self):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.return_value = self.mock_user_llm

        await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.mock_user_llm.reveal.assert_called_once_with(
            crypto_client=self.mock_crypto_client,
            organization_id=self.organization_id,
            user_id=self.user_id,
        )

    async def test_returns_config_built_from_repo_on_cache_miss(self):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.return_value = self.mock_user_llm

        result = await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.assertIsInstance(result, UserLlmConfig)
        self.assertEqual(result.api_base, self.mock_user_llm.api_base)
        self.assertEqual(result.max_tokens, self.mock_user_llm.max_tokens)

    async def test_sets_cache_after_repo_fetch(self):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.return_value = self.mock_user_llm

        await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.mock_cache_service.set_user_llm_config.assert_awaited_once()
        call_kwargs = self.mock_cache_service.set_user_llm_config.call_args.kwargs
        self.assertEqual(call_kwargs['user_identity'], self.user_identity)
        self.assertIsInstance(call_kwargs['response'], UserLlmConfig)


    async def test_raises_user_llm_get_failed(self):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.side_effect = UserLlmGetFailed('db error')

        with self.assertRaises(UserLlmGetFailed):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

    async def test_raises_unexpected_error(self):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.side_effect = RuntimeError('unexpected')

        with self.assertRaises(RuntimeError):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

    async def test_does_not_set_cache_on_repo_error(self):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.side_effect = UserLlmGetFailed('db error')

        with self.assertRaises(UserLlmGetFailed):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

        self.mock_cache_service.set_user_llm_config.assert_not_awaited()

    async def test_raises_when_cache_get_fails(self):
        self.mock_cache_service.get_user_llm_config.side_effect = RuntimeError('redis down')

        with self.assertRaises(RuntimeError):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

    async def test_raises_when_crypto_factory_fails(self):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.return_value = self.mock_user_llm
        self.mock_crypto_client_factory.side_effect = RuntimeError('vault unreachable')

        with self.assertRaises(RuntimeError):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)


    @patch(f'{MODULE}.logger')
    async def test_logs_db_error_with_exc_info(self, mock_logger):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.side_effect = UserLlmGetFailed('db error')

        with self.assertRaises(UserLlmGetFailed):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Get user llm failed', log_call.args[0])
        self.assertTrue(log_call.kwargs['exc_info'])

    @patch(f'{MODULE}.logger')
    async def test_logs_db_error_context(self, mock_logger):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.side_effect = UserLlmGetFailed('db error')

        with self.assertRaises(UserLlmGetFailed):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

        extra = mock_logger.error.call_args.kwargs['extra']
        self.assertEqual(extra['organization_id'], self.organization_id)
        self.assertEqual(extra['user_id'], self.user_id)
        self.assertEqual(extra['error_type'], 'UserLlmGetFailed')

    @patch(f'{MODULE}.logger')
    async def test_logs_unexpected_error_with_exc_info(self, mock_logger):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.side_effect = ValueError('unexpected')

        with self.assertRaises(ValueError):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Unexpected error', log_call.args[0])
        self.assertTrue(log_call.kwargs['exc_info'])

    @patch(f'{MODULE}.logger')
    async def test_logs_unexpected_error_context(self, mock_logger):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.side_effect = ValueError('unexpected')

        with self.assertRaises(ValueError):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

        extra = mock_logger.error.call_args.kwargs['extra']
        self.assertEqual(extra['org_id'], str(self.organization_id))
        self.assertEqual(extra['user_id'], str(self.user_id))
        self.assertEqual(extra['error_type'], 'ValueError')

    @patch(f'{MODULE}.logger')
    async def test_cache_get_failure_logs_unexpected_error(self, mock_logger):
        self.mock_cache_service.get_user_llm_config.side_effect = RuntimeError('redis down')

        with self.assertRaises(RuntimeError):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

        mock_logger.error.assert_called_once()
        self.assertIn('Unexpected error', mock_logger.error.call_args.args[0])

    @patch(f'{MODULE}.logger')
    async def test_crypto_factory_failure_logs_unexpected_error(self, mock_logger):
        self.mock_cache_service.get_user_llm_config.return_value = None
        self.mock_repo.get_user_llm.return_value = self.mock_user_llm
        self.mock_crypto_client_factory.side_effect = RuntimeError('vault unreachable')

        with self.assertRaises(RuntimeError):
            await self.service.get_user_llm_config(self.user_identity, self.model_id)

        extra = mock_logger.error.call_args.kwargs['extra']
        self.assertEqual(extra['error_type'], 'RuntimeError')
