import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from sqlalchemy.exc import SQLAlchemyError

from database.exceptions import (
    IntegrationGetFailed, 
    IntegrationNotFound, 
    IntegrationDeleteFailed, 
    IntegrationCreateFailed, 
    IntegrationUpdateFailed
)
from database.repositories.integration_repository import IntegrationRepository



def _make_async_session_scope(session):
    ctx = AsyncMock()
    ctx.__aenter__.return_value = session
    ctx.__aexit__.return_value = None
    return ctx


class TestIntegrationRepository(unittest.IsolatedAsyncioTestCase):

    async def test_get_user_integration_ids_success(self):
        org_id, user_id = uuid4(), uuid4()

        result = Mock()
        id1, id2 = uuid4(), uuid4()
        result.all.return_value = [(id1,), (id2,)]
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        ids = await repo.get_user_integration_ids(user_id=user_id, organization_id=org_id)
        self.assertEqual(ids, [id1, id2])
        session.execute.assert_awaited_once()

    async def test_get_user_integration_ids_db_error_raises_IntegrationGetFailed(self):
        org_id, user_id = uuid4(), uuid4()
        session = MagicMock()
        session.execute = AsyncMock(side_effect=SQLAlchemyError('db down'))
        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with self.assertRaises(IntegrationGetFailed):
            await repo.get_user_integration_ids(user_id=user_id, organization_id=org_id)

    async def test_get_integration_success(self):
        org_id, user_id, integ_id = uuid4(), uuid4(), str(uuid4())

        orm_obj = SimpleNamespace()
        result = Mock()
        result.scalar_one_or_none.return_value = orm_obj
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with patch.object(repo, '_to_encrypted_integration', return_value='encrypted') as conv:
            val = await repo.get_integration(user_id=user_id, organization_id=org_id, integration_id=integ_id)

        self.assertEqual(val, 'encrypted')
        conv.assert_called_once_with(orm_obj)

    async def test_get_integration_not_found_raises_IntegrationNotFound(self):
        org_id, user_id, integ_id = uuid4(), uuid4(), str(uuid4())

        result = Mock()
        result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with self.assertRaises(IntegrationNotFound):
            await repo.get_integration(user_id=user_id, organization_id=org_id, integration_id=integ_id)

    async def test_get_integration_db_error_raises_IntegrationGetFailed(self):
        org_id, user_id, integ_id = uuid4(), uuid4(), str(uuid4())

        session = MagicMock()
        session.execute = AsyncMock(side_effect=SQLAlchemyError('boom'))
        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with self.assertRaises(IntegrationGetFailed):
            await repo.get_integration(user_id=user_id, organization_id=org_id, integration_id=integ_id)

    async def test_get_integration_by_id_success(self):
        org_id, user_id, integ_id = uuid4(), uuid4(), uuid4()

        orm_obj = SimpleNamespace()
        result = Mock()
        result.scalar_one_or_none.return_value = orm_obj
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with patch.object(repo, '_to_encrypted_integration', return_value='encrypted') as conv:
            val = await repo.get_integration_by_id(user_id=user_id, organization_id=org_id, integration_id=integ_id)

        self.assertEqual(val, 'encrypted')
        conv.assert_called_once_with(orm_obj)

    async def test_get_integration_by_id_not_found_raises(self):
        from database.exceptions import IntegrationNotFound

        org_id, user_id, integ_id = uuid4(), uuid4(), uuid4()

        result = Mock()
        result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with self.assertRaises(IntegrationNotFound):
            await repo.get_integration_by_id(user_id=user_id, organization_id=org_id, integration_id=integ_id)

    @patch('database.repositories.integration_repository.IntegrationORM')
    async def test_create_integration_success(self, mock_integration_orm_cls):
        org_id, user_id = uuid4(), uuid4()
        encrypted = SimpleNamespace(
            organization_id=org_id,
            user_id=user_id,
            service_type='postgres',
            auth_method='password',
            connection_name='analytics',
            host='db.local',
            port=5432,
            database_name='analytics_db',
            encrypted_username=b'...',
            encrypted_password=b'...',
            encrypted_kerberos_principal=None,
            encrypted_windows_domain=None,
            encrypted_extra_options=b'...',
            autosync_on=True,
        )

        new_id = uuid4()
        orm_instance = SimpleNamespace(id=new_id)
        mock_integration_orm_cls.return_value = orm_instance

        session = MagicMock()
        session.add = Mock()
        session.flush = AsyncMock()
        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        got_id = await repo.create_integration(organization_id=org_id, user_id=user_id, encrypted_integration=encrypted)
        self.assertEqual(got_id, new_id)
        session.add.assert_called_once_with(orm_instance)
        session.flush.assert_awaited_once()

    async def test_create_integration_db_error_raises_IntegrationCreateFailed(self):
        org_id, user_id = uuid4(), uuid4()
        encrypted = SimpleNamespace(
            organization_id=org_id,
            user_id=user_id,
            service_type='postgres',
            auth_method='password',
            connection_name='analytics',
            host='db.local',
            port=5432,
            database_name='analytics_db',
            encrypted_username=b'...',
            encrypted_password=b'...',
            encrypted_kerberos_principal=None,
            encrypted_windows_domain=None,
            encrypted_extra_options=b'...',
            autosync_on=True,
        )

        session = MagicMock()
        session.add = Mock()
        session.flush = AsyncMock(side_effect=SQLAlchemyError('db oops'))
        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with self.assertRaises(IntegrationCreateFailed):
            await repo.create_integration(organization_id=org_id, user_id=user_id, encrypted_integration=encrypted)

    async def test_update_integration_success(self):
        org_id, user_id, integ_id = uuid4(), uuid4(), uuid4()

        result = SimpleNamespace(rowcount=1)
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        await repo.update_integration(
            integration_id=integ_id,
            user_id=user_id,
            organization_id=org_id,
            update_args={'connection_name': 'new', 'autosync_on': False},
        )
        session.execute.assert_awaited_once()

    async def test_update_integration_zero_rowcount_raises(self):
        org_id, user_id, integ_id = uuid4(), uuid4(), uuid4()
        result = SimpleNamespace(rowcount=0)
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with self.assertRaises(IntegrationUpdateFailed):
            await repo.update_integration(
                integration_id=integ_id,
                user_id=user_id,
                organization_id=org_id,
                update_args={'connection_name': 'x'},
            )

    async def test_delete_integration_success(self):
        org_id, user_id, integ_id = uuid4(), uuid4(), str(uuid4())

        result = SimpleNamespace(rowcount=1)
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        await repo.delete_integration(user_id=user_id, organization_id=org_id, integration_id=integ_id)
        session.execute.assert_awaited_once()

    async def test_delete_integration_zero_rowcount_raises(self):
        org_id, user_id, integ_id = uuid4(), uuid4(), str(uuid4())

        result = SimpleNamespace(rowcount=0)
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with self.assertRaises(IntegrationDeleteFailed):
            await repo.delete_integration(user_id=user_id, organization_id=org_id, integration_id=integ_id)

    async def test_delete_integration_db_error_raises(self):
        org_id, user_id, integ_id = uuid4(), uuid4(), str(uuid4())

        session = MagicMock()
        session.execute = AsyncMock(side_effect=SQLAlchemyError('boom'))

        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        with self.assertRaises(IntegrationDeleteFailed):
            await repo.delete_integration(user_id=user_id, organization_id=org_id, integration_id=integ_id)

    @patch('database.repositories.integration_repository.IntegrationProfile')
    async def test_get_user_integration_profiles_success(self, mock_profile_cls):
        org_id, user_id = uuid4(), uuid4()

        orm1 = SimpleNamespace(
            id=uuid4(),
            service_type='postgres',
            connection_name='analytics',
            database_name='db1',
            auth_method='password',
            autosync_on=True,
        )
        orm2 = SimpleNamespace(
            id=uuid4(),
            service_type='mysql',
            connection_name='bi',
            database_name='db2',
            auth_method='password',
            autosync_on=False,
        )

        scalars = Mock()
        scalars.all.return_value = [orm1, orm2]
        result = Mock()
        result.scalars.return_value = scalars

        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        db = SimpleNamespace(session_scope=Mock(return_value=_make_async_session_scope(session)))
        repo = IntegrationRepository(db)

        mock_profile_cls.side_effect = lambda **kwargs: kwargs

        out = await repo.get_user_integration_profiles(user_id=user_id, organization_id=org_id)

        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]['id'], orm1.id)
        self.assertEqual(out[1]['connection_name'], orm2.connection_name)
        self.assertEqual(mock_profile_cls.call_count, 2)

