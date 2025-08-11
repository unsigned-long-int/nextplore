import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from api.handlers.handle_delete import handle_vector_delete


def make_event(org_id=111, user_id=222, integration_id=333):
    return types.SimpleNamespace(
        organization_id=org_id,
        user_id=user_id,
        integration_id=integration_id,
    )


class TestHandleVectorDelete(unittest.IsolatedAsyncioTestCase):
    @patch('api.handlers.handle_delete.VectorRepository')
    @patch('api.handlers.handle_delete.delete_pg_vector_metadata', new_callable=AsyncMock)
    @patch('api.handlers.handle_delete.delete_qdrant_vectors', new_callable=AsyncMock)
    @patch('api.handlers.handle_delete.vector_service_cache')
    async def test_happy_path(self, mock_cache, mock_del_qdrant, mock_del_pg, repo_ctor):
        event = make_event()
        connector = MagicMock(name='DatabaseBackendConnector')

        vector_repo_instance = MagicMock()
        vector_repo_instance.get_qdrant_vector_ids = AsyncMock(return_value=[1, 2, 3])
        repo_ctor.return_value = vector_repo_instance

        mock_cache.delete_by_prefix = AsyncMock()

        await handle_vector_delete(event, connector)

        repo_ctor.assert_called_once_with(connector)

        vector_repo_instance.get_qdrant_vector_ids.assert_awaited_once_with(
            organization_id=event.organization_id,
            user_id=event.user_id,
            integration_id=event.integration_id,
        )

        mock_del_pg.assert_awaited_once_with(
            connector=connector,
            organization_id=event.organization_id,
            user_id=event.user_id,
            integration_id=event.integration_id,
        )

        mock_del_qdrant.assert_awaited_once_with(
            qdrant_vector_ids=['1', '2', '3'],
            user_id=str(event.user_id),
            organization_id=str(event.organization_id),
        )

        mock_cache.delete_by_prefix.assert_awaited_once_with(
            event.organization_id, event.user_id
        )

    @patch('api.handlers.handle_delete.VectorRepository')
    @patch('api.handlers.handle_delete.delete_pg_vector_metadata', new_callable=AsyncMock)
    @patch('api.handlers.handle_delete.delete_qdrant_vectors', new_callable=AsyncMock)
    @patch('api.handlers.handle_delete.vector_service_cache')
    async def test_empty_vector_list(self, mock_cache, mock_del_qdrant, mock_del_pg, repo_ctor):
        event = make_event()
        connector = MagicMock()

        vector_repo_instance = MagicMock()
        vector_repo_instance.get_qdrant_vector_ids = AsyncMock(return_value=[])
        repo_ctor.return_value = vector_repo_instance

        mock_cache.delete_by_prefix = AsyncMock()

        await handle_vector_delete(event, connector)

        vector_repo_instance.get_qdrant_vector_ids.assert_awaited_once()

        mock_del_pg.assert_awaited_once_with(
            connector=connector,
            organization_id=event.organization_id,
            user_id=event.user_id,
            integration_id=event.integration_id,
        )
        mock_del_qdrant.assert_awaited_once_with(
            qdrant_vector_ids=[],
            user_id=str(event.user_id),
            organization_id=str(event.organization_id),
        )
        mock_cache.delete_by_prefix.assert_awaited_once_with(
            event.organization_id, event.user_id
        )
