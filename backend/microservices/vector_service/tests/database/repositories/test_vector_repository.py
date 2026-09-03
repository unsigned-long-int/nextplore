import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from vector_service.database.exceptions import (
    VectorCountGetFailed,
    VectorDeleteFailed,
    VectorGetFailed,
    VectorProfilesGetFailed,
    VectorUpsertFailed,
)
from vector_service.database.repositories import VectorRepository

MAPPER = (
    "vector_service.database.repositories.vector_repository."
    "orm_to_domain_vector_profile"
)


class VectorRepositoryTestBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.backend_connector_mock = MagicMock()
        self.session_mock = AsyncMock()
        scope_cm = self.backend_connector_mock.session_scope.return_value
        scope_cm.__aenter__.return_value = self.session_mock

        self.repository = VectorRepository(
            backend_connector=self.backend_connector_mock
        )

        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.datastore_id = uuid4()

    def assert_session_scoped_to_tenant(self):
        """Every query must open a session bound to the caller's tenant.

        This is the contract row-level security depends on: if the repository
        ever opens an unscoped session, RLS has nothing to filter on.
        """
        self.backend_connector_mock.session_scope.assert_called_once_with(
            self.organization_id, self.user_id
        )


class TestGetProfiles(VectorRepositoryTestBase):
    async def test_returns_mapped_profiles(self):
        vector_orms = [MagicMock(), MagicMock()]
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = vector_orms
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        self.session_mock.execute.return_value = result_mock

        with patch(MAPPER) as mapper_mock:
            mapper_mock.side_effect = lambda orm: f"profile-{id(orm)}"

            result = await self.repository.get_profiles(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
            )

        self.assertEqual(len(result), 2)
        self.assertEqual(mapper_mock.call_count, 2)
        self.session_mock.execute.assert_awaited_once()
        self.assert_session_scoped_to_tenant()

    async def test_returns_empty_list_when_no_rows(self):
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
        )

        self.assertEqual(result, [])

    async def test_returns_empty_list_without_querying_when_datastore_id_missing(self):
        result = await self.repository.get_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=None,
        )

        self.assertEqual(result, [])
        self.session_mock.execute.assert_not_awaited()
        self.backend_connector_mock.session_scope.assert_not_called()

    async def test_raises_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError("boom")

        with self.assertRaises(VectorProfilesGetFailed) as ctx:
            await self.repository.get_profiles(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
            )

        self.assertIn("Get vector profiles failed", str(ctx.exception))

    async def test_database_error_is_chained(self):
        original = SQLAlchemyError("boom")
        self.session_mock.execute.side_effect = original

        with self.assertRaises(VectorProfilesGetFailed) as ctx:
            await self.repository.get_profiles(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
            )

        self.assertIs(ctx.exception.__cause__, original)


class TestGetVectors(VectorRepositoryTestBase):
    async def test_returns_rows(self):
        rows = [MagicMock(), MagicMock(), MagicMock()]
        result_mock = MagicMock()
        result_mock.all.return_value = rows
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_vectors(
            organization_id=self.organization_id,
            user_id=self.user_id,
            vector_ids=[uuid4(), uuid4(), uuid4()],
        )

        self.assertEqual(result, rows)
        self.session_mock.execute.assert_awaited_once()
        self.assert_session_scoped_to_tenant()

    async def test_returns_empty_list_without_querying_when_no_ids(self):
        result = await self.repository.get_vectors(
            organization_id=self.organization_id,
            user_id=self.user_id,
            vector_ids=[],
        )

        self.assertEqual(result, [])
        self.session_mock.execute.assert_not_awaited()
        self.backend_connector_mock.session_scope.assert_not_called()

    async def test_raises_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError("boom")

        with self.assertRaises(VectorGetFailed) as ctx:
            await self.repository.get_vectors(
                organization_id=self.organization_id,
                user_id=self.user_id,
                vector_ids=[uuid4()],
            )

        self.assertIn("Get vectors failed", str(ctx.exception))


class TestGetVectorCount(VectorRepositoryTestBase):
    async def test_returns_count(self):
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 42
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_vector_count(
            organization_id=self.organization_id, user_id=self.user_id
        )

        self.assertEqual(result, 42)
        self.assert_session_scoped_to_tenant()

    async def test_returns_zero(self):
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 0
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_vector_count(
            organization_id=self.organization_id, user_id=self.user_id
        )

        self.assertEqual(result, 0)

    async def test_raises_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError("boom")

        with self.assertRaises(VectorCountGetFailed) as ctx:
            await self.repository.get_vector_count(
                organization_id=self.organization_id, user_id=self.user_id
            )

        self.assertIn("Get vector count failed", str(ctx.exception))


class TestUpsertVectorMeta(VectorRepositoryTestBase):
    async def test_adds_and_flushes(self):
        vectors_orm = [MagicMock(), MagicMock()]

        await self.repository.upsert_vector_meta(
            organization_id=self.organization_id,
            user_id=self.user_id,
            vectors_orm=vectors_orm,
        )

        self.session_mock.add_all.assert_called_once_with(vectors_orm)
        self.session_mock.flush.assert_awaited_once()
        self.assert_session_scoped_to_tenant()

    async def test_empty_list_still_flushes(self):
        await self.repository.upsert_vector_meta(
            organization_id=self.organization_id,
            user_id=self.user_id,
            vectors_orm=[],
        )

        self.session_mock.add_all.assert_called_once_with([])
        self.session_mock.flush.assert_awaited_once()

    async def test_raises_on_database_error(self):
        self.session_mock.flush.side_effect = SQLAlchemyError("boom")

        with self.assertRaises(VectorUpsertFailed) as ctx:
            await self.repository.upsert_vector_meta(
                organization_id=self.organization_id,
                user_id=self.user_id,
                vectors_orm=[MagicMock()],
            )

        self.assertIn("Upsert vectors failed", str(ctx.exception))


class TestDeleteVectorMeta(VectorRepositoryTestBase):
    async def test_executes_delete(self):
        await self.repository.delete_vector_meta(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
        )

        self.session_mock.execute.assert_awaited_once()
        self.assert_session_scoped_to_tenant()

    async def test_raises_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError("boom")

        with self.assertRaises(VectorDeleteFailed) as ctx:
            await self.repository.delete_vector_meta(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
            )

        self.assertIn("Delete vectors failed", str(ctx.exception))


class TestGetQdrantVectorIds(VectorRepositoryTestBase):
    async def test_returns_ids(self):
        qdrant_ids = [uuid4(), uuid4()]
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = qdrant_ids
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_qdrant_vector_ids(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
        )

        self.assertEqual(result, qdrant_ids)
        self.assert_session_scoped_to_tenant()

    async def test_returns_empty_list(self):
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_qdrant_vector_ids(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
        )

        self.assertEqual(result, [])

    async def test_database_error_propagates_unwrapped(self):
        self.session_mock.execute.side_effect = SQLAlchemyError("boom")

        with self.assertRaises(SQLAlchemyError):
            await self.repository.get_qdrant_vector_ids(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
            )
