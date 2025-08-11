import uuid
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from services.pg.delete.pg_delete_service import delete_pg_vector_metadata


class TestDeletePgVectorMetadata(unittest.IsolatedAsyncioTestCase):
    @patch('services.pg.delete.pg_delete_service.VectorRepository')
    async def test_calls_repo_with_correct_args(self, repo_ctor):
        connector = MagicMock(name='DatabaseBackendConnector')
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        integration_id = uuid.uuid4()

        repo_instance = MagicMock(name='VectorRepositoryInstance')
        repo_instance.delete_vector_meta = AsyncMock()
        repo_ctor.return_value = repo_instance

        await delete_pg_vector_metadata(
            connector=connector,
            organization_id=org_id,
            user_id=user_id,
            integration_id=integration_id,
        )

        repo_ctor.assert_called_once_with(connector)
        repo_instance.delete_vector_meta.assert_awaited_once_with(
            organization_id=org_id,
            user_id=user_id,
            integration_id=integration_id,
        )

    @patch('services.pg.delete.pg_delete_service.VectorRepository')
    async def test_propagates_repo_exception(self, repo_ctor):
        connector = MagicMock()
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        integration_id = uuid.uuid4()

        repo_instance = MagicMock()
        err = RuntimeError('DB error')
        repo_instance.delete_vector_meta = AsyncMock(side_effect=err)
        repo_ctor.return_value = repo_instance

        with self.assertRaises(RuntimeError) as ctx:
            await delete_pg_vector_metadata(
                connector=connector,
                organization_id=org_id,
                user_id=user_id,
                integration_id=integration_id,
            )
        self.assertIs(ctx.exception, err)

        repo_ctor.assert_called_once_with(connector)
        repo_instance.delete_vector_meta.assert_awaited_once()
