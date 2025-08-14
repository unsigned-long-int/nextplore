import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from services.qdrant.upsert.qdrant_upsert_service import upsert_qdrant_vectors


class FakePointStruct:
    def __init__(self, id, vector, payload):
        self.id = id
        self.vector = vector
        self.payload = payload


class TestUpsertQdrantVectors(unittest.IsolatedAsyncioTestCase):
    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'https://qdrant.local', 'QDRANT_API_KEY': 'sekret'})
    @patch('services.qdrant.upsert.qdrant_upsert_service.AsyncQdrantClient')
    @patch('services.qdrant.upsert.qdrant_upsert_service.PointStruct', side_effect=lambda **kw: FakePointStruct(**kw))
    async def test_happy_path_builds_points_and_calls_upsert(self, mock_point_struct, mock_client_cls):
        p1 = SimpleNamespace(
            id=uuid.UUID('11111111-1111-1111-1111-111111111111'),
            vector=[0.1, 0.2, 0.3],
            user_id=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
            organization_id=uuid.UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),
        )
        p2 = SimpleNamespace(
            id=uuid.UUID('22222222-2222-2222-2222-222222222222'),
            vector=[0.9, 0.8, 0.7],
            user_id=uuid.UUID('cccccccc-cccc-cccc-cccc-cccccccccccc'),
            organization_id=uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddddd'),
        )

        client = MagicMock()
        client.upsert = AsyncMock(return_value=None)
        mock_client_cls.return_value = client

        await upsert_qdrant_vectors([p1, p2])

        mock_client_cls.assert_called_once_with(url='https://qdrant.local', api_key='sekret')

        client.upsert.assert_awaited_once()
        _, kwargs = client.upsert.call_args
        self.assertEqual(kwargs['collection_name'], 'nextplore')
        points = kwargs['points']
        self.assertEqual(len(points), 2)
        self.assertTrue(all(isinstance(pt, FakePointStruct) for pt in points))

        pt1 = points[0]
        self.assertEqual(pt1.id, str(p1.id))
        self.assertEqual(pt1.vector, p1.vector)
        self.assertEqual(
            pt1.payload,
            {
                'qdrant_vector_id': str(p1.id),
                'user_id': str(p1.user_id),
                'organization_id': str(p1.organization_id),
            },
        )

        pt2 = points[1]
        self.assertEqual(pt2.id, str(p2.id))
        self.assertEqual(
            pt2.payload['qdrant_vector_id'],
            str(p2.id),
        )

    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'https://qdrant.local', 'QDRANT_API_KEY': 'sekret'})
    @patch('services.qdrant.upsert.qdrant_upsert_service.AsyncQdrantClient')
    @patch('services.qdrant.upsert.qdrant_upsert_service.PointStruct', side_effect=lambda **kw: FakePointStruct(**kw))
    async def test_empty_input_calls_upsert_with_empty_points(self, _mock_point_struct, mock_client_cls):
        client = MagicMock()
        client.upsert = AsyncMock(return_value=None)
        mock_client_cls.return_value = client

        await upsert_qdrant_vectors([])

        client.upsert.assert_awaited_once()
        _, kwargs = client.upsert.call_args
        self.assertEqual(kwargs['collection_name'], 'nextplore')
        self.assertEqual(kwargs['points'], [])

    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'https://qdrant.local', 'QDRANT_API_KEY': 'sekret'})
    @patch('services.qdrant.upsert.qdrant_upsert_service.AsyncQdrantClient')
    @patch('services.qdrant.upsert.qdrant_upsert_service.PointStruct', side_effect=lambda **kw: FakePointStruct(**kw))
    async def test_client_exception_propagates(self, _mock_point_struct, mock_client_cls):
        client = MagicMock()
        client.upsert = AsyncMock(side_effect=RuntimeError('qdrant down'))
        mock_client_cls.return_value = client

        with self.assertRaises(RuntimeError):
            await upsert_qdrant_vectors([SimpleNamespace(id=uuid.uuid4(), vector=[0.1], user_id=uuid.uuid4(), organization_id=uuid.uuid4())])

        client.upsert.assert_awaited_once()
