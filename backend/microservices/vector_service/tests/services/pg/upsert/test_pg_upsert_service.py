import uuid
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from services.pg.upsert.pg_upsert_service import upsert_pg_vector_metadata


class TestUpsertPgVectorMetadata(unittest.IsolatedAsyncioTestCase):
    @patch('services.pg.upsert.pg_upsert_service.VectorRepository')
    async def test_calls_repo_with_correct_args(self, repo_ctor):
        connector = MagicMock(name='DatabaseBackendConnector')
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        vectors_orm = [MagicMock(name='VectorORM#1'), MagicMock(name='VectorORM#2')]

        repo_instance = MagicMock(name='VectorRepositoryInstance')
        repo_instance.upsert_vector_meta = AsyncMock()
        repo_ctor.return_value = repo_instance

        await upsert_pg_vector_metadata(
            connector=connector,
            organization_id=org_id,
            user_id=user_id,
            vectors_orm=vectors_orm,
        )

        repo_ctor.assert_called_once_with(connector)
        repo_instance.upsert_vector_meta.assert_awaited_once_with(
            organization_id=org_id,
            user_id=user_id,
            vectors_orm=vectors_orm,
        )

    @patch('services.pg.upsert.pg_upsert_service.VectorRepository')
    async def test_propagates_repo_exception(self, repo_ctor):
        connector = MagicMock()
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        vectors_orm = [MagicMock()]

        repo_instance = MagicMock()
        err = RuntimeError('DB error')
        repo_instance.upsert_vector_meta = AsyncMock(side_effect=err)
        repo_ctor.return_value = repo_instance

        with self.assertRaises(RuntimeError) as ctx:
            await upsert_pg_vector_metadata(
                connector=connector,
                organization_id=org_id,
                user_id=user_id,
                vectors_orm=vectors_orm,
            )
        self.assertIs(ctx.exception, err)

        repo_ctor.assert_called_once_with(connector)
        repo_instance.upsert_vector_meta.assert_awaited_once_with(
            organization_id=org_id,
            user_id=user_id,
            vectors_orm=vectors_orm,
        )
