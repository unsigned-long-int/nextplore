import types
import uuid
import unittest
from unittest.mock import AsyncMock, MagicMock

from services.vector_store_service.store.store_service import VectorStoreService
from services.vector_store_service.exceptions import (
    DeleteVectorDBFailed,
    SearchVectorDBFailed,
    UpsertVectorDBFailed,
)


def make_identity(org_id=111, user_id=222):
    return types.SimpleNamespace(organization_id=org_id, user_id=user_id)


def make_vector_points(n=2):
    return [
        types.SimpleNamespace(
            id=uuid.uuid4(),
            user_id=222,
            organization_id=111,
            vector=[0.1, 0.2, 0.3],
        )
        for _ in range(n)
    ]


class TestVectorStoreService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = MagicMock()
        self.client.delete_vectors = AsyncMock()
        self.client.search_nearest_vectors = AsyncMock()
        self.client.upsert_vectors = AsyncMock()
        self.client.aclose = AsyncMock()
        self.svc = VectorStoreService(self.client)

    async def test_delete_vectors_happy_path(self):
        await self.svc.delete_vectors(['a', 'b'], user_id='u1', organization_id='o1')
        self.client.delete_vectors.assert_awaited_once_with(['a', 'b'], 'u1', 'o1')

    async def test_delete_vectors_reraises_specific(self):
        self.client.delete_vectors.side_effect = DeleteVectorDBFailed('nope')
        with self.assertRaises(DeleteVectorDBFailed):
            await self.svc.delete_vectors(['x'], user_id='u', organization_id='o')

    async def test_delete_vectors_wraps_generic(self):
        self.client.delete_vectors.side_effect = RuntimeError('boom')
        with self.assertRaises(DeleteVectorDBFailed) as ctx:
            await self.svc.delete_vectors(['x'], user_id='u', organization_id='o')
        self.assertIn('boom', str(ctx.exception))
        self.assertIn('MagicMock', str(ctx.exception))

    async def test_search_nearest_vectors_happy_path(self):
        expected = [uuid.uuid4(), uuid.uuid4()]
        self.client.search_nearest_vectors.return_value = expected
        ident = make_identity()
        emb = [0.9, 0.8]
        out = await self.svc.search_nearest_vectors(ident, emb, top_k=3)
        self.assertIs(out, expected)
        self.client.search_nearest_vectors.assert_awaited_once_with(ident, emb, 3)

    async def test_search_nearest_vectors_reraises_specific(self):
        self.client.search_nearest_vectors.side_effect = SearchVectorDBFailed('bad')
        with self.assertRaises(SearchVectorDBFailed):
            await self.svc.search_nearest_vectors(make_identity(), [0.1], top_k=1)

    async def test_search_nearest_vectors_wraps_generic(self):
        self.client.search_nearest_vectors.side_effect = ValueError('uh oh')
        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await self.svc.search_nearest_vectors(make_identity(), [0.1, 0.2], top_k=2)
        self.assertIn('uh oh', str(ctx.exception))
        self.assertIn('MagicMock', str(ctx.exception))

    async def test_upsert_vectors_happy_path(self):
        vps = make_vector_points(2)
        await self.svc.upsert_vectors(vps)
        self.client.upsert_vectors.assert_awaited_once_with(vps)

    async def test_upsert_vectors_reraises_specific(self):
        self.client.upsert_vectors.side_effect = UpsertVectorDBFailed('nope')
        with self.assertRaises(UpsertVectorDBFailed):
            await self.svc.upsert_vectors(make_vector_points(1))

    async def test_upsert_vectors_wraps_generic(self):
        self.client.upsert_vectors.side_effect = RuntimeError('kaputt')
        with self.assertRaises(UpsertVectorDBFailed) as ctx:
            await self.svc.upsert_vectors(make_vector_points(1))
        self.assertIn('kaputt', str(ctx.exception))
        self.assertIn('MagicMock', str(ctx.exception))

    async def test_aclose_calls_client(self):
        await self.svc.aclose()
        self.client.aclose.assert_awaited_once()

    async def test_aclose_swallows_exception(self):
        self.client.aclose.side_effect = RuntimeError('ignore')
        await self.svc.aclose()
