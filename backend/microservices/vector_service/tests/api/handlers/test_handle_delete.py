import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from integration_service.api.handlers import handle_vector_delete


def make_event(org_id=111, user_id=222, integration_id=333):
    return types.SimpleNamespace(
        organization_id=org_id,
        user_id=user_id,
        integration_id=integration_id,
    )


class TestHandleVectorDelete(unittest.IsolatedAsyncioTestCase):
    @patch('api.handlers.handle_delete.VectorRepository')
    async def test_happy_path(self, repo_ctor):
        event = make_event()
        connector = MagicMock(name='DatabaseBackendConnector')

        vector_repo_instance = MagicMock()
        vector_repo_instance.get_qdrant_vector_ids = AsyncMock(return_value=[1, 2, 3])
        vector_repo_instance.delete_vector_meta = AsyncMock()
        repo_ctor.return_value = vector_repo_instance

        cache_service = MagicMock()
        cache_service.cache = MagicMock()
        cache_service.cache.delete_by_prefix = AsyncMock()

        vector_store_service = MagicMock()
        vector_store_service.delete_vectors = AsyncMock()

        await handle_vector_delete(event, connector, cache_service, vector_store_service)

        repo_ctor.assert_called_once_with(connector)

        vector_repo_instance.get_qdrant_vector_ids.assert_awaited_once_with(
            organization_id=event.organization_id,
            user_id=event.user_id,
            integration_id=event.integration_id,
        )

        vector_repo_instance.delete_vector_meta.assert_awaited_once_with(
            organization_id=event.organization_id,
            user_id=event.user_id,
            integration_id=event.integration_id,
        )

        vector_store_service.delete_vectors.assert_awaited_once_with(
            vector_ids=['1', '2', '3'],
            user_id=str(event.user_id),
            organization_id=str(event.organization_id),
        )

        cache_service.cache.delete_by_prefix.assert_awaited_once_with(
            event.organization_id, event.user_id
        )

    @patch('api.handlers.handle_delete.VectorRepository')
    async def test_empty_vector_list(self, repo_ctor):
        event = make_event()
        connector = MagicMock()

        vector_repo_instance = MagicMock()
        vector_repo_instance.get_qdrant_vector_ids = AsyncMock(return_value=[])
        vector_repo_instance.delete_vector_meta = AsyncMock()
        repo_ctor.return_value = vector_repo_instance

        cache_service = MagicMock()
        cache_service.cache = MagicMock()
        cache_service.cache.delete_by_prefix = AsyncMock()

        vector_store_service = MagicMock()
        vector_store_service.delete_vectors = AsyncMock()

        await handle_vector_delete(event, connector, cache_service, vector_store_service)

        vector_repo_instance.get_qdrant_vector_ids.assert_awaited_once_with(
            organization_id=event.organization_id,
            user_id=event.user_id,
            integration_id=event.integration_id,
        )

        vector_repo_instance.delete_vector_meta.assert_awaited_once_with(
            organization_id=event.organization_id,
            user_id=event.user_id,
            integration_id=event.integration_id,
        )

        vector_store_service.delete_vectors.assert_awaited_once_with(
            vector_ids=[],
            user_id=str(event.user_id),
            organization_id=str(event.organization_id),
        )

        cache_service.cache.delete_by_prefix.assert_awaited_once_with(
            event.organization_id, event.user_id
        )
