import types
import uuid
import unittest
from unittest.mock import AsyncMock, patch
from httpx import Headers
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from ai_orm_context_service.services import QDrantStoreClient
from ai_orm_context_service.services import (
    DeleteVectorDBFailed,
    SearchVectorDBFailed,
    UpsertVectorDBFailed,
)


def make_identity(org_id=111, user_id=222):
    return types.SimpleNamespace(organization_id=org_id, user_id=user_id)


def make_vector_point(id_str=None, user_id=222, org_id=111, vector=None):
    return types.SimpleNamespace(
        id=uuid.UUID(id_str) if id_str else uuid.uuid4(),
        user_id=user_id,
        organization_id=org_id,
        vector=vector if vector is not None else [0.1, 0.2, 0.3],
    )


class TestQDrantStoreClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.cluster_host = 'https://qdrant.local'
        self.api_key = 'secret'

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_search_returns_uuid_list(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client

        uid = make_identity()
        emb = [0.9, 0.8, 0.7]
        v1 = str(uuid.uuid4())
        v2 = str(uuid.uuid4())
        mock_client.search.return_value = [
            types.SimpleNamespace(payload={'qdrant_vector_id': v1}),
            types.SimpleNamespace(payload={'qdrant_vector_id': v2}),
        ]

        client = QDrantStoreClient(self.cluster_host, self.api_key)

        result = await client.search_nearest_vectors(uid, emb, top_k=2, collection='nextplore')

        self.assertEqual([uuid.UUID(v1), uuid.UUID(v2)], result)
        mock_client.search.assert_awaited_once()
        _, kwargs = mock_client.search.call_args
        self.assertEqual(kwargs['collection_name'], 'nextplore')
        self.assertEqual(kwargs['query_vector'], emb)
        self.assertEqual(kwargs['limit'], 2)
        self.assertTrue(kwargs['with_payload'])
        self.assertFalse(kwargs['with_vectors'])
        self.assertIsNotNone(kwargs['query_filter'])

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_search_empty_returns_empty_list(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client
        mock_client.search.return_value = []

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        result = await client.search_nearest_vectors(make_identity(), [0.1, 0.2, 0.3])

        self.assertEqual([], result)
        mock_client.search.assert_awaited_once()

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_search_maps_response_handling_exception(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client
        mock_client.search.side_effect = ResponseHandlingException('bad payload')

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        with self.assertRaises(SearchVectorDBFailed):
            await client.search_nearest_vectors(make_identity(), [0.1, 0.2, 0.3])

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_search_maps_unexpected_response(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client

        err = UnexpectedResponse(
            503,
            'Service Unavailable',
            b'oops',
            Headers({})
        )
        mock_client.search.side_effect = err

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await client.search_nearest_vectors(make_identity(), [0.1, 0.2, 0.3])

        self.assertIn('status code 503', str(ctx.exception))

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_search_maps_generic_exception(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client
        mock_client.search.side_effect = RuntimeError('boom')

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        with self.assertRaises(SearchVectorDBFailed):
            await client.search_nearest_vectors(make_identity(), [0.1, 0.2, 0.3])

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_delete_vectors_success(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        ids = ['a', 'b', 'c']

        await client.delete_vectors(ids, user_id='222', organization_id='111', collection='nextplore')

        mock_client.delete.assert_awaited_once()
        _, kwargs = mock_client.delete.call_args
        self.assertEqual(kwargs['collection_name'], 'nextplore')
        self.assertIn('points_selector', kwargs)
        self.assertIsNotNone(kwargs['points_selector'])

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_delete_vectors_maps_exception(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client
        mock_client.delete.side_effect = ValueError('nope')

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        with self.assertRaises(DeleteVectorDBFailed):
            await client.delete_vectors(['x'], user_id='1', organization_id='2')

    @patch('services.vector_store_service.clients.qdrant_store_client.PointStruct')
    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_upsert_vectors_success_builds_points(self, mock_client_ctor, mock_pointstruct):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client

        mock_pointstruct.side_effect = lambda **kwargs: kwargs

        vp1 = make_vector_point(id_str='11111111-1111-1111-1111-111111111111', vector=[1.0, 1.1])
        vp2 = make_vector_point(id_str='22222222-2222-2222-2222-222222222222', vector=[2.0, 2.2])

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        await client.upsert_vectors([vp1, vp2], collection='nextplore')

        mock_client.upsert.assert_awaited_once()
        _, kwargs = mock_client.upsert.call_args
        self.assertEqual(kwargs['collection_name'], 'nextplore')

        points = kwargs['points']
        self.assertEqual(points[0]['id'], str(vp1.id))
        self.assertEqual(points[0]['vector'], vp1.vector)
        self.assertEqual(
            points[0]['payload'],
            {
                'qdrant_vector_id': str(vp1.id),
                'user_id': str(vp1.user_id),
                'organization_id': str(vp1.organization_id),
            },
        )
        self.assertEqual(points[1]['id'], str(vp2.id))
        self.assertEqual(points[1]['vector'], vp2.vector)

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_upsert_vectors_maps_exception(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client
        mock_client.upsert.side_effect = RuntimeError('fail')

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        with self.assertRaises(UpsertVectorDBFailed):
            await client.upsert_vectors([make_vector_point()])

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_aclose_calls_client_close(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client_ctor.return_value = mock_client

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        await client.aclose()

        mock_client.close.assert_awaited_once()

    @patch('services.vector_store_service.clients.qdrant_store_client.AsyncQdrantClient')
    async def test_aclose_swallows_exception(self, mock_client_ctor):
        mock_client = AsyncMock()
        mock_client.close.side_effect = RuntimeError('ignore')
        mock_client_ctor.return_value = mock_client

        client = QDrantStoreClient(self.cluster_host, self.api_key)
        await client.aclose()
