import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from api.router.get_qdrant_vectors_router import get_qdrant_vectors


def make_payload(embedding=None):
    return types.SimpleNamespace(
        embedding=[0.1, 0.2, 0.3] if embedding is None else embedding
    )


class GetQdrantVectorsTests(unittest.IsolatedAsyncioTestCase):
    @patch('api.router.get_qdrant_vectors_router.get_current_identity')
    async def test_cache_hit(self, mock_identity):
        user_identity = 'user-xyz'
        mock_identity.return_value = user_identity

        payload = make_payload()

        cache_service = MagicMock()
        cache_service.get_qdrant_vectors = AsyncMock(return_value={'vector_ids': [42]})
        cache_service.set_qdrant_vectors = AsyncMock()

        vector_store_service = MagicMock()
        vector_store_service.search_nearest_vectors = AsyncMock()

        result = await get_qdrant_vectors(
            payload,
            cache_service=cache_service,
            vector_store_service=vector_store_service
        )

        self.assertIs(result, cache_service.get_qdrant_vectors.return_value)

        cache_service.get_qdrant_vectors.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
        )
        vector_store_service.search_nearest_vectors.assert_not_awaited()
        cache_service.set_qdrant_vectors.assert_not_awaited()

    @patch('api.router.get_qdrant_vectors_router.QDrantVectorResponse')
    @patch('api.router.get_qdrant_vectors_router.get_current_identity')
    async def test_cache_miss_builds_and_sets_cache(self, mock_identity, mock_resp_cls):
        user_identity = {'sub': 'abc'}
        mock_identity.return_value = user_identity

        payload = make_payload([0.9, 0.8])

        cache_service = MagicMock()
        cache_service.get_qdrant_vectors = AsyncMock(return_value=None)
        cache_service.set_qdrant_vectors = AsyncMock()

        found_ids = [10, 11, 12]
        vector_store_service = MagicMock()
        vector_store_service.search_nearest_vectors = AsyncMock(return_value=found_ids)

        response_instance = MagicMock(name='QDrantVectorResponseInstance')
        mock_resp_cls.return_value = response_instance

        result = await get_qdrant_vectors(
            payload,
            cache_service=cache_service,
            vector_store_service=vector_store_service
        )

        cache_service.get_qdrant_vectors.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
        )
        vector_store_service.search_nearest_vectors.assert_awaited_once_with(
            user_identity,
            payload.embedding
        )

        mock_resp_cls.assert_called_once_with(vector_ids=found_ids)
        self.assertIs(result, response_instance)

        cache_service.set_qdrant_vectors.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
            response=response_instance,
        )
