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
    @patch('api.router.get_qdrant_vectors_router.vector_service_cache')
    @patch('api.router.get_qdrant_vectors_router.search_nearest_vectors', new_callable=AsyncMock)
    @patch('api.router.get_qdrant_vectors_router.QDrantVectorResponse')
    async def test_cache_hit(self, mock_resp_cls, mock_search, mock_cache, mock_identity):
        user_identity = 'user-xyz'
        mock_identity.return_value = user_identity

        payload = make_payload()
        cached_response = {'vector_ids': [42]}
        mock_cache.get_qdrant_vectors = AsyncMock(return_value=cached_response)
        mock_cache.set_qdrant_vectors = AsyncMock()

        result = await get_qdrant_vectors(payload)

        self.assertIs(result, cached_response)

        mock_cache.get_qdrant_vectors.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
        )

        mock_search.assert_not_awaited()
        mock_resp_cls.assert_not_called()
        mock_cache.set_qdrant_vectors.assert_not_awaited()

    @patch('api.router.get_qdrant_vectors_router.get_current_identity')
    @patch('api.router.get_qdrant_vectors_router.vector_service_cache')
    @patch('api.router.get_qdrant_vectors_router.search_nearest_vectors', new_callable=AsyncMock)
    @patch('api.router.get_qdrant_vectors_router.QDrantVectorResponse')
    async def test_cache_miss_builds_and_sets_cache(self, mock_resp_cls, mock_search, mock_cache, mock_identity):
        user_identity = {'sub': 'abc'}
        mock_identity.return_value = user_identity

        payload = make_payload([0.9, 0.8])
        mock_cache.get_qdrant_vectors = AsyncMock(return_value=None)
        mock_cache.set_qdrant_vectors = AsyncMock()

        found_ids = [10, 11, 12]
        mock_search.return_value = found_ids

        response_instance = MagicMock(name='QDrantVectorResponseInstance')
        mock_resp_cls.return_value = response_instance

        result = await get_qdrant_vectors(payload)

        mock_cache.get_qdrant_vectors.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
        )
        mock_search.assert_awaited_once_with(user_identity, payload.embedding)

        mock_resp_cls.assert_called_once_with(vector_ids=found_ids)
        self.assertIs(result, response_instance)

        mock_cache.set_qdrant_vectors.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
            response=response_instance,
        )
