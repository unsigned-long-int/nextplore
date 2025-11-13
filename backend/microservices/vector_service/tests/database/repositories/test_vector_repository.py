import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from integration_service.database import VectorRepository


class _FakeSelectQuery:
    def __init__(self, label='SELECT'):
        self.label = label

    def where(self, *args, **kwargs):
        return _FakeSelectQuery(label=f'{self.label}.WHERE')

    def select_from(self, *args, **kwargs):
        return self


class _FakeDeleteQuery:
    def __init__(self, label='DELETE'):
        self.label = label

    def where(self, *args, **kwargs):
        return _FakeDeleteQuery(label=f'{self.label}.WHERE')


def _make_connector_with_session(scoped_session):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=scoped_session)
    cm.__aexit__ = AsyncMock(return_value=None)
    connector = MagicMock()
    connector.session_scope.return_value = cm
    return connector, cm


class TestVectorRepository(unittest.IsolatedAsyncioTestCase):
    async def test_get_vector_profiles_returns_empty_if_no_integration_id(self):
        connector = MagicMock()
        repo = VectorRepository(connector)

        rows = await repo.get_vector_profiles(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            integration_id=None,
        )

        self.assertEqual(rows, [])
        connector.session_scope.assert_not_called()

    @patch('database.repositories.vector_repository.select', side_effect=lambda *args, **kw: _FakeSelectQuery())
    async def test_get_vector_profiles_queries_and_returns_rows(self, _mock_select):
        scoped_session = MagicMock()
        result = MagicMock()
        mocked_rows = [MagicMock(), MagicMock()]
        result.all.return_value = mocked_rows
        scoped_session.execute = AsyncMock(return_value=result)

        connector, _ = _make_connector_with_session(scoped_session)
        repo = VectorRepository(connector)

        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        integration_id = uuid.uuid4()

        rows = await repo.get_vector_profiles(org_id, user_id, integration_id)

        connector.session_scope.assert_called_once_with(org_id, user_id)
        scoped_session.execute.assert_awaited_once()
        self.assertIs(rows, mocked_rows)

    async def test_get_vectors_returns_empty_if_no_ids(self):
        connector = MagicMock()
        repo = VectorRepository(connector)

        rows = await repo.get_vectors(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            vector_ids=[],
        )

        self.assertEqual(rows, [])
        connector.session_scope.assert_not_called()

    @patch('database.repositories.vector_repository.select', side_effect=lambda *args, **kw: _FakeSelectQuery())
    async def test_get_vectors_queries_and_returns_rows(self, _mock_select):
        scoped_session = MagicMock()
        result = MagicMock()
        mocked_rows = [MagicMock(), MagicMock(), MagicMock()]
        result.all.return_value = mocked_rows
        scoped_session.execute = AsyncMock(return_value=result)
        connector, _ = _make_connector_with_session(scoped_session)
        repo = VectorRepository(connector)

        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        ids = [uuid.uuid4(), uuid.uuid4()]

        rows = await repo.get_vectors(org_id, user_id, ids)

        connector.session_scope.assert_called_once_with(org_id, user_id)
        scoped_session.execute.assert_awaited_once()
        self.assertIs(rows, mocked_rows)

    @patch('database.repositories.vector_repository.select', side_effect=lambda *args, **kw: _FakeSelectQuery())
    @patch('database.repositories.vector_repository.func')
    async def test_get_vector_count_returns_scalar(self, mock_func, _mock_select):
        fake_count_query = _FakeSelectQuery(label='COUNT')
        mock_func.count.return_value = fake_count_query

        scoped_session = MagicMock()
        result = MagicMock()
        result.scalar_one.return_value = 7
        scoped_session.execute = AsyncMock(return_value=result)
        connector, _ = _make_connector_with_session(scoped_session)
        repo = VectorRepository(connector)

        org_id = uuid.uuid4()
        user_id = uuid.uuid4()

        count = await repo.get_vector_count(org_id, user_id)

        connector.session_scope.assert_called_once_with(org_id, user_id)
        scoped_session.execute.assert_awaited_once()
        result.scalar_one.assert_called_once()
        self.assertEqual(count, 7)

    async def test_upsert_vector_meta_adds_and_flushes(self):
        scoped_session = MagicMock()
        scoped_session.add_all = MagicMock()
        scoped_session.flush = AsyncMock()
        connector, _ = _make_connector_with_session(scoped_session)
        repo = VectorRepository(connector)

        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        vectors_orm = [MagicMock(), MagicMock()]

        await repo.upsert_vector_meta(org_id, user_id, vectors_orm)

        connector.session_scope.assert_called_once_with(org_id, user_id)
        scoped_session.add_all.assert_called_once_with(vectors_orm)
        scoped_session.flush.assert_awaited_once()

    @patch('database.repositories.vector_repository.delete', side_effect=lambda *args, **kw: _FakeDeleteQuery())
    async def test_delete_vector_meta_executes_delete(self, _mock_delete):
        scoped_session = MagicMock()
        scoped_session.execute = AsyncMock()
        connector, _ = _make_connector_with_session(scoped_session)
        repo = VectorRepository(connector)

        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        integration_id = uuid.uuid4()

        await repo.delete_vector_meta(org_id, user_id, integration_id)

        connector.session_scope.assert_called_once_with(org_id, user_id)
        scoped_session.execute.assert_awaited_once()
        arg = scoped_session.execute.call_args.args[0]
        self.assertIsInstance(arg, _FakeDeleteQuery)
        self.assertTrue(arg.label.startswith('DELETE.WHERE'))

    @patch('database.repositories.vector_repository.select', side_effect=lambda *args, **kw: _FakeSelectQuery())
    async def test_get_qdrant_vector_ids_returns_list(self, _mock_select):
        scalars_obj = MagicMock()
        expected = [uuid.uuid4(), uuid.uuid4()]
        scalars_obj.all.return_value = expected

        result = MagicMock()
        result.scalars.return_value = scalars_obj

        scoped_session = MagicMock()
        scoped_session.execute = AsyncMock(return_value=result)

        connector, _ = _make_connector_with_session(scoped_session)
        repo = VectorRepository(connector)

        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        integration_id = uuid.uuid4()

        out = await repo.get_qdrant_vector_ids(org_id, user_id, integration_id)

        connector.session_scope.assert_called_once_with(org_id, user_id)
        scoped_session.execute.assert_awaited_once()
        result.scalars.assert_called_once()
        scalars_obj.all.assert_called_once()
        self.assertIs(out, expected)
