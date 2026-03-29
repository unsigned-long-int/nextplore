import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from integration_service.api.context import UserIdentity
from integration_service.database.exceptions import UserLlmCreateFailed, UserLlmGetFailed
from integration_service.database.repositories import LlmRepository
from integration_service.services.llm import LlmService
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from svc_integration_contracts.models import UserLlmCreateRequest


MODULE = 'integration_service.services.llm.llm_service'


def make_user_identity(**overrides) -> UserIdentity:
    defaults = {
        'organization_id': uuid4(),
        'user_id': uuid4(),
    }
    return UserIdentity(**{**defaults, **overrides})


def make_payload(**overrides) -> UserLlmCreateRequest:
    defaults = {
        'kek_kid': 'https://vault.azure.net/keys/test-key/version',
        'model_id': 'openai/meta-llama/Llama-3.1-8B-Instruct',
        'api_base': 'https://router.huggingface.co/v1',
        'max_tokens': 4096,
        'label': 'My Llama endpoint',
        'connection_params': {
            'api_key': 'hf-test-key',
        },
    }
    return UserLlmCreateRequest(**{**defaults, **overrides})


def make_service(repo, cache_service=None, crypto_client_factory=None) -> LlmService:
    return LlmService(
        repo=repo,
        cache_service=cache_service or AsyncMock(),
        crypto_client_factory=crypto_client_factory or MagicMock(),
    )


class TestLlmServiceCreate(unittest.IsolatedAsyncioTestCase):

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
        self.payload = make_payload()

    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_success_calls_crypto_client_factory_with_kek_kid(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.return_value = self.model_id

        await self.service.create_user_llm(self.user_identity, self.payload)

        self.mock_crypto_client_factory.assert_called_once_with(self.payload.kek_kid)

    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_success_calls_from_dto_with_correct_args(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.return_value = self.model_id

        await self.service.create_user_llm(self.user_identity, self.payload)

        mock_from_dto.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            payload=self.payload,
            crypto_client=self.mock_crypto_client,
        )

    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_success_creates_user_llm_in_repo(self, mock_from_dto):
        llm_domain = MagicMock()
        mock_from_dto.return_value = llm_domain
        self.mock_repo.create_user_llm.return_value = self.model_id

        await self.service.create_user_llm(self.user_identity, self.payload)

        self.mock_repo.create_user_llm.assert_awaited_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            user_llm=llm_domain,
        )

    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_success_invalidates_cache_after_create(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.return_value = self.model_id

        await self.service.create_user_llm(self.user_identity, self.payload)

        self.mock_cache_service.delete_user_llm_profiles.assert_awaited_once_with(
            self.user_identity
        )

    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_success_call_order(self, mock_from_dto):
        call_order = []
        mock_from_dto.side_effect = lambda **kw: call_order.append('from_dto') or MagicMock()

        async def track_create(**kw):
            call_order.append('create_repo')
            return self.model_id

        self.mock_repo.create_user_llm.side_effect = track_create

        await self.service.create_user_llm(self.user_identity, self.payload)

        self.assertEqual(call_order, ['from_dto', 'create_repo'])

    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_llm_create_failed_raises(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.side_effect = UserLlmCreateFailed('db error')

        with self.assertRaises(UserLlmCreateFailed):
            await self.service.create_user_llm(self.user_identity, self.payload)

    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_unexpected_error_raises(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.side_effect = RuntimeError('unexpected')

        with self.assertRaises(RuntimeError):
            await self.service.create_user_llm(self.user_identity, self.payload)

    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_llm_create_failed_does_not_invalidate_cache(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.side_effect = UserLlmCreateFailed('db error')

        with self.assertRaises(UserLlmCreateFailed):
            await self.service.create_user_llm(self.user_identity, self.payload)

        self.mock_cache_service.delete_user_llm_profiles.assert_not_awaited()

    @patch(f'{MODULE}.logger')
    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_llm_create_failed_logs_error(self, mock_from_dto, mock_logger):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.side_effect = UserLlmCreateFailed('db error')

        with self.assertRaises(UserLlmCreateFailed):
            await self.service.create_user_llm(self.user_identity, self.payload)

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Create user llm failed', log_call.args[0])
        self.assertTrue(log_call.kwargs['exc_info'])

    @patch(f'{MODULE}.logger')
    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_llm_create_failed_logs_context(self, mock_from_dto, mock_logger):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.side_effect = UserLlmCreateFailed('db error')

        with self.assertRaises(UserLlmCreateFailed):
            await self.service.create_user_llm(self.user_identity, self.payload)

        extra = mock_logger.error.call_args.kwargs['extra']
        self.assertEqual(extra['organization_id'], self.organization_id)
        self.assertEqual(extra['user_id'], self.user_id)
        self.assertEqual(extra['error_type'], 'UserLlmCreateFailed')
        self.assertIsNone(extra['model_id'])

    @patch(f'{MODULE}.logger')
    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_unexpected_error_logs_error(self, mock_from_dto, mock_logger):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.side_effect = ValueError('unexpected')

        with self.assertRaises(ValueError):
            await self.service.create_user_llm(self.user_identity, self.payload)

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Unexpected error', log_call.args[0])
        self.assertTrue(log_call.kwargs['exc_info'])

    @patch(f'{MODULE}.logger')
    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_unexpected_error_logs_context(self, mock_from_dto, mock_logger):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.side_effect = ValueError('unexpected')

        with self.assertRaises(ValueError):
            await self.service.create_user_llm(self.user_identity, self.payload)

        extra = mock_logger.error.call_args.kwargs['extra']
        self.assertEqual(extra['user_id'], str(self.user_id))
        self.assertEqual(extra['error_type'], 'ValueError')
        self.assertIsNone(extra['model_id'])

    @patch(f'{MODULE}.logger')
    async def test_crypto_client_factory_failure_logs_unexpected_error(self, mock_logger):
        self.mock_crypto_client_factory.side_effect = RuntimeError('vault unreachable')

        with self.assertRaises(RuntimeError):
            await self.service.create_user_llm(self.user_identity, self.payload)

        extra = mock_logger.error.call_args.kwargs['extra']
        self.assertEqual(extra['error_type'], 'RuntimeError')

    @patch(f'{MODULE}.user_llm_from_dto')
    async def test_custom_kek_kid_passed_to_factory(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_user_llm.return_value = self.model_id
        custom_kek = 'https://custom.vault.com/keys/k/v2'
        payload = make_payload(kek_kid=custom_kek)

        await self.service.create_user_llm(self.user_identity, payload)

        self.mock_crypto_client_factory.assert_called_once_with(custom_kek)


class TestLlmServiceGetProfiles(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_repo = AsyncMock(spec=LlmRepository)
        self.mock_cache_service = AsyncMock()

        self.service = LlmService(
            repo=self.mock_repo,
            cache_service=self.mock_cache_service,
            crypto_client_factory=MagicMock(),
        )

        self.user_identity = make_user_identity()
        self.organization_id = self.user_identity.organization_id
        self.user_id = self.user_identity.user_id

        self.mock_profiles = [MagicMock(), MagicMock()]


    async def test_returns_cached_profiles_when_cache_hit(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = self.mock_profiles

        result = await self.service.get_user_llm_profiles(self.user_identity)

        self.assertEqual(result, self.mock_profiles)

    async def test_does_not_call_repo_when_cache_hit(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = self.mock_profiles

        await self.service.get_user_llm_profiles(self.user_identity)

        self.mock_repo.get_user_llm_profiles.assert_not_awaited()

    async def test_does_not_set_cache_when_cache_hit(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = self.mock_profiles

        await self.service.get_user_llm_profiles(self.user_identity)

        self.mock_cache_service.set_user_llm_profiles.assert_not_awaited()

    async def test_calls_cache_get_with_user_identity(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = self.mock_profiles

        await self.service.get_user_llm_profiles(self.user_identity)

        self.mock_cache_service.get_user_llm_profiles.assert_awaited_once_with(
            self.user_identity
        )


    async def test_calls_repo_when_cache_miss(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.return_value = self.mock_profiles

        await self.service.get_user_llm_profiles(self.user_identity)

        self.mock_repo.get_user_llm_profiles.assert_awaited_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
        )

    async def test_returns_repo_profiles_on_cache_miss(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.return_value = self.mock_profiles

        result = await self.service.get_user_llm_profiles(self.user_identity)

        self.assertEqual(result, self.mock_profiles)

    async def test_sets_cache_after_repo_fetch(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.return_value = self.mock_profiles

        await self.service.get_user_llm_profiles(self.user_identity)

        self.mock_cache_service.set_user_llm_profiles.assert_awaited_once_with(
            self.user_identity,
            self.mock_profiles
        )

    async def test_returns_empty_list_when_repo_returns_none(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.return_value = []

        result = await self.service.get_user_llm_profiles(self.user_identity)

        self.assertEqual(result, [])


    async def test_raises_user_llm_get_failed(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.side_effect = UserLlmGetFailed('db error')

        with self.assertRaises(UserLlmGetFailed):
            await self.service.get_user_llm_profiles(self.user_identity)

    async def test_raises_unexpected_error(self):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.side_effect = RuntimeError('unexpected')

        with self.assertRaises(RuntimeError):
            await self.service.get_user_llm_profiles(self.user_identity)

    @patch(f'{MODULE}.logger')
    async def test_logs_db_error_with_exc_info(self, mock_logger):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.side_effect = UserLlmGetFailed('db error')

        with self.assertRaises(UserLlmGetFailed):
            await self.service.get_user_llm_profiles(self.user_identity)

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Get user llm profiles failed', log_call.args[0])
        self.assertTrue(log_call.kwargs['exc_info'])

    @patch(f'{MODULE}.logger')
    async def test_logs_db_error_context(self, mock_logger):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.side_effect = UserLlmGetFailed('db error')

        with self.assertRaises(UserLlmGetFailed):
            await self.service.get_user_llm_profiles(self.user_identity)

        extra = mock_logger.error.call_args.kwargs['extra']
        self.assertEqual(extra['organization_id'], self.organization_id)
        self.assertEqual(extra['user_id'], self.user_id)
        self.assertEqual(extra['error_type'], 'UserLlmGetFailed')

    @patch(f'{MODULE}.logger')
    async def test_logs_unexpected_error_with_exc_info(self, mock_logger):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.side_effect = ValueError('unexpected')

        with self.assertRaises(ValueError):
            await self.service.get_user_llm_profiles(self.user_identity)

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Unexpected error', log_call.args[0])
        self.assertTrue(log_call.kwargs['exc_info'])

    @patch(f'{MODULE}.logger')
    async def test_logs_unexpected_error_context(self, mock_logger):
        self.mock_cache_service.get_user_llm_profiles.return_value = None
        self.mock_repo.get_user_llm_profiles.side_effect = ValueError('unexpected')

        with self.assertRaises(ValueError):
            await self.service.get_user_llm_profiles(self.user_identity)

        extra = mock_logger.error.call_args.kwargs['extra']
        self.assertEqual(extra['user_id'], str(self.user_id))
        self.assertEqual(extra['error_type'], 'ValueError')

    @patch(f'{MODULE}.logger')
    async def test_cache_get_failure_raises_and_logs_unexpected(self, mock_logger):
        self.mock_cache_service.get_user_llm_profiles.side_effect = RuntimeError('redis down')

        with self.assertRaises(RuntimeError):
            await self.service.get_user_llm_profiles(self.user_identity)

        mock_logger.error.assert_called_once()
        self.assertIn('Unexpected error', mock_logger.error.call_args.args[0])