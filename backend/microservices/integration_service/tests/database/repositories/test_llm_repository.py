import unittest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from integration_service.database.exceptions import UserLlmCreateFailed, UserLlmGetFailed
from integration_service.database.repositories.llm_repository import LlmRepository
from integration_service.domain.models.user_llm import UserLlm, UserLlmProfile


MODULE = 'integration_service.database.repositories.llm_repository'


def make_backend_connector():
    connector = MagicMock()
    session = AsyncMock()
    connector.session_scope.return_value.__aenter__ = AsyncMock(return_value=session)
    connector.session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
    return connector, session


def make_user_llm_orm(**overrides):
    orm = MagicMock()
    orm.id = uuid4()
    orm.api_base = 'https://api.openai.com/v1'
    orm.model_id = 'gpt-4o'
    orm.label = 'GPT-4o'
    orm.max_tokens = 4096
    for k, v in overrides.items():
        setattr(orm, k, v)
    return orm


def make_user_llm_profile(**overrides):
    defaults = {
        'api_base': 'https://api.openai.com/v1',
        'model_id': 'gpt-4o',
        'label': 'GPT-4o',
        'max_tokens': 4096,
    }
    return UserLlmProfile(**{**defaults, **overrides})


class TestLlmRepositoryCreate(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.user_llm = MagicMock(spec=UserLlm)
        self.connector, self.session = make_backend_connector()
        self.repo = LlmRepository(self.connector)

    @patch(f'{MODULE}.orm_from_user_llm')
    async def test_returns_model_id(self, mock_orm_from_user_llm):
        model_id = uuid4()
        orm = make_user_llm_orm(id=model_id)
        mock_orm_from_user_llm.return_value = orm

        result = await self.repo.create_user_llm(
            organization_id=self.organization_id,
            user_id=self.user_id,
            user_llm=self.user_llm,
        )

        self.assertEqual(result, model_id)

    @patch(f'{MODULE}.orm_from_user_llm')
    async def test_calls_orm_from_user_llm_with_correct_args(self, mock_orm_from_user_llm):
        orm = make_user_llm_orm()
        mock_orm_from_user_llm.return_value = orm

        await self.repo.create_user_llm(
            organization_id=self.organization_id,
            user_id=self.user_id,
            user_llm=self.user_llm,
        )

        mock_orm_from_user_llm.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            user_llm=self.user_llm,
        )

    @patch(f'{MODULE}.orm_from_user_llm')
    async def test_adds_orm_to_session(self, mock_orm_from_user_llm):
        orm = make_user_llm_orm()
        mock_orm_from_user_llm.return_value = orm

        await self.repo.create_user_llm(
            organization_id=self.organization_id,
            user_id=self.user_id,
            user_llm=self.user_llm,
        )

        self.session.add.assert_called_once_with(orm)

    @patch(f'{MODULE}.orm_from_user_llm')
    async def test_flushes_session(self, mock_orm_from_user_llm):
        orm = make_user_llm_orm()
        mock_orm_from_user_llm.return_value = orm

        await self.repo.create_user_llm(
            organization_id=self.organization_id,
            user_id=self.user_id,
            user_llm=self.user_llm,
        )

        self.session.flush.assert_awaited_once()

    @patch(f'{MODULE}.orm_from_user_llm')
    async def test_opens_session_scope_with_correct_ids(self, mock_orm_from_user_llm):
        mock_orm_from_user_llm.return_value = make_user_llm_orm()

        await self.repo.create_user_llm(
            organization_id=self.organization_id,
            user_id=self.user_id,
            user_llm=self.user_llm,
        )

        self.connector.session_scope.assert_called_once_with(
            self.organization_id, self.user_id
        )

    @patch(f'{MODULE}.orm_from_user_llm')
    async def test_raises_user_llm_create_failed_on_sqlalchemy_error(self, mock_orm_from_user_llm):
        mock_orm_from_user_llm.return_value = make_user_llm_orm()
        self.session.flush.side_effect = SQLAlchemyError('db error')

        with self.assertRaises(UserLlmCreateFailed):
            await self.repo.create_user_llm(
                organization_id=self.organization_id,
                user_id=self.user_id,
                user_llm=self.user_llm,
            )

    @patch(f'{MODULE}.orm_from_user_llm')
    async def test_error_message_contains_db_error(self, mock_orm_from_user_llm):
        mock_orm_from_user_llm.return_value = make_user_llm_orm()
        self.session.flush.side_effect = SQLAlchemyError('constraint violation')

        with self.assertRaises(UserLlmCreateFailed) as ctx:
            await self.repo.create_user_llm(
                organization_id=self.organization_id,
                user_id=self.user_id,
                user_llm=self.user_llm,
            )

        self.assertIn('constraint violation', str(ctx.exception))

    @patch(f'{MODULE}.logger')
    @patch(f'{MODULE}.orm_from_user_llm')
    async def test_logs_error_on_sqlalchemy_error(self, mock_orm_from_user_llm, mock_logger):
        mock_orm_from_user_llm.return_value = make_user_llm_orm()
        self.session.flush.side_effect = SQLAlchemyError('db error')

        with self.assertRaises(UserLlmCreateFailed):
            await self.repo.create_user_llm(
                organization_id=self.organization_id,
                user_id=self.user_id,
                user_llm=self.user_llm,
            )

        mock_logger.error.assert_called_once()
        self.assertTrue(mock_logger.error.call_args.kwargs['exc_info'])


class TestLlmRepositoryGetProfiles(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.connector, self.session = make_backend_connector()
        self.repo = LlmRepository(self.connector)

    def _mock_query_result(self, orm_list):
        result = MagicMock()
        result.scalars.return_value.all.return_value = orm_list
        self.session.execute = AsyncMock(return_value=result)

    @patch(f'{MODULE}.user_llm_profile_from_orm')
    async def test_returns_mapped_profiles(self, mock_profile_from_orm):
        orm1 = make_user_llm_orm()
        orm2 = make_user_llm_orm(model_id='claude-3-5-sonnet')
        self._mock_query_result([orm1, orm2])

        profile1 = make_user_llm_profile()
        profile2 = make_user_llm_profile(model_id='claude-3-5-sonnet')
        mock_profile_from_orm.side_effect = [profile1, profile2]

        result = await self.repo.get_user_llm_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id,
        )

        self.assertEqual(result, [profile1, profile2])

    @patch(f'{MODULE}.user_llm_profile_from_orm')
    async def test_calls_profile_from_orm_for_each_record(self, mock_profile_from_orm):
        orm1 = make_user_llm_orm()
        orm2 = make_user_llm_orm()
        self._mock_query_result([orm1, orm2])
        mock_profile_from_orm.return_value = make_user_llm_profile()

        await self.repo.get_user_llm_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id,
        )

        self.assertEqual(mock_profile_from_orm.call_count, 2)
        mock_profile_from_orm.assert_any_call(orm1)
        mock_profile_from_orm.assert_any_call(orm2)

    @patch(f'{MODULE}.user_llm_profile_from_orm')
    async def test_returns_empty_list_when_no_records(self, mock_profile_from_orm):
        self._mock_query_result([])

        result = await self.repo.get_user_llm_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id,
        )

        self.assertEqual(result, [])
        mock_profile_from_orm.assert_not_called()

    @patch(f'{MODULE}.user_llm_profile_from_orm')
    async def test_opens_session_scope_with_correct_ids(self, mock_profile_from_orm):
        self._mock_query_result([])

        await self.repo.get_user_llm_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id,
        )

        self.connector.session_scope.assert_called_once_with(
            self.organization_id, self.user_id
        )

    async def test_raises_user_llm_get_failed_on_sqlalchemy_error(self):
        self.session.execute = AsyncMock(side_effect=SQLAlchemyError('db error'))

        with self.assertRaises(UserLlmGetFailed):
            await self.repo.get_user_llm_profiles(
                organization_id=self.organization_id,
                user_id=self.user_id,
            )

    async def test_error_message_contains_db_error(self):
        self.session.execute = AsyncMock(side_effect=SQLAlchemyError('timeout'))

        with self.assertRaises(UserLlmGetFailed) as ctx:
            await self.repo.get_user_llm_profiles(
                organization_id=self.organization_id,
                user_id=self.user_id,
            )

        self.assertIn('timeout', str(ctx.exception))

    @patch(f'{MODULE}.logger')
    async def test_logs_error_on_sqlalchemy_error(self, mock_logger):
        self.session.execute = AsyncMock(side_effect=SQLAlchemyError('db error'))

        with self.assertRaises(UserLlmGetFailed):
            await self.repo.get_user_llm_profiles(
                organization_id=self.organization_id,
                user_id=self.user_id,
            )

        mock_logger.error.assert_called_once()
        self.assertTrue(mock_logger.error.call_args.kwargs['exc_info'])