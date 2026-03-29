import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from typing import List


from kafka_messaging.events.embedding_service import CrawlMetaEmbedded
from vector_service.services.vector_store_service.exceptions import UpsertVectorDBFailed
from vector_service.database.exceptions import VectorUpsertFailed
from vector_service.api.handlers import handle_vector_upsert


class MockTableMeta:
    def __init__(self, columns: List[str], description: str):
        self.columns = columns
        self.description = description

    def model_dump_json(self) -> str:
        return f"{{'columns': {self.columns}, 'description': '{self.description}'}}"


class MockORMEmbedding:

    def __init__(
            self,
            datastore_id: UUID,
            schema_name: str,
            table_name: str,
            table_meta: MockTableMeta,
            embedding: List[float]
    ):
        self.datastore_id = datastore_id
        self.schema_name = schema_name
        self.table_name = table_name
        self.table_meta = table_meta
        self.embedding = embedding


class TestHandleVectorUpsert(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.datastore_id = uuid4()

        self.table_meta_1 = MockTableMeta(
            columns=['id', 'name', 'email'],
            description='Users table'
        )
        self.table_meta_2 = MockTableMeta(
            columns=['id', 'user_id', 'amount'],
            description='Orders table'
        )

        self.orm_embeddings = [
            MockORMEmbedding(
                datastore_id=self.datastore_id,
                schema_name='public',
                table_name='users',
                table_meta=self.table_meta_1,
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5]
            ),
            MockORMEmbedding(
                datastore_id=self.datastore_id,
                schema_name='public',
                table_name='orders',
                table_meta=self.table_meta_2,
                embedding=[0.6, 0.7, 0.8, 0.9, 1.0]
            )
        ]

        self.event = MagicMock(spec=CrawlMetaEmbedded)
        self.event.organization_id = self.organization_id
        self.event.user_id = self.user_id
        self.event.orm_embedding = self.orm_embeddings

        self.backend_connector = MagicMock()
        self.cache_service = MagicMock()
        self.cache_service.cache = MagicMock()
        self.cache_service.cache.delete_by_prefix = AsyncMock()
        self.vector_store_service = MagicMock()
        self.vector_store_service.upsert_vectors = AsyncMock()

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    @patch('vector_service.api.handlers.handle_upsert.uuid.uuid4')
    async def test_handle_vector_upsert_success(
            self, mock_uuid4, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.upsert_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        mock_uuid_1 = uuid4()
        mock_uuid_2 = uuid4()
        mock_uuid4.side_effect = [mock_uuid_1, mock_uuid_2]

        await handle_vector_upsert(
            event=self.event,
            backend_connector=self.backend_connector,
            cache_service=self.cache_service,
            vector_store_service=self.vector_store_service
        )

        mock_vector_repo_class.assert_called_once_with(self.backend_connector)

        mock_vector_repo.upsert_vector_meta.assert_called_once()
        call_kwargs = mock_vector_repo.upsert_vector_meta.call_args[1]
        self.assertEqual(call_kwargs['organization_id'], self.organization_id)
        self.assertEqual(call_kwargs['user_id'], self.user_id)

        pg_vectors = call_kwargs['vectors_orm']
        self.assertEqual(len(pg_vectors), 2)

        self.assertEqual(pg_vectors[0].user_id, self.user_id)
        self.assertEqual(pg_vectors[0].organization_id, self.organization_id)
        self.assertEqual(pg_vectors[0].qdrant_vector_id, mock_uuid_1)
        self.assertEqual(pg_vectors[0].datastore_id, self.datastore_id)
        self.assertEqual(pg_vectors[0].schema_name, 'public')
        self.assertEqual(pg_vectors[0].table_name, 'users')
        self.assertIn('Users table', pg_vectors[0].table_meta)

        self.assertEqual(pg_vectors[1].qdrant_vector_id, mock_uuid_2)
        self.assertEqual(pg_vectors[1].table_name, 'orders')

        self.vector_store_service.upsert_vectors.assert_called_once()
        qdrant_vectors = self.vector_store_service.upsert_vectors.call_args[1]['vector_points']
        self.assertEqual(len(qdrant_vectors), 2)

        self.assertEqual(qdrant_vectors[0].id, mock_uuid_1)
        self.assertEqual(qdrant_vectors[0].user_id, self.user_id)
        self.assertEqual(qdrant_vectors[0].organization_id, self.organization_id)
        self.assertEqual(qdrant_vectors[0].vector, [0.1, 0.2, 0.3, 0.4, 0.5])

        self.assertEqual(qdrant_vectors[1].id, mock_uuid_2)
        self.assertEqual(qdrant_vectors[1].vector, [0.6, 0.7, 0.8, 0.9, 1.0])

        self.cache_service.cache.delete_by_prefix.assert_called_once_with(
            self.organization_id,
            self.user_id
        )

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    async def test_handle_vector_upsert_with_empty_embeddings(
            self, mock_vector_repo_class
    ):
        self.event.orm_embedding = []
        mock_vector_repo = MagicMock()
        mock_vector_repo.upsert_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        await handle_vector_upsert(
            event=self.event,
            backend_connector=self.backend_connector,
            cache_service=self.cache_service,
            vector_store_service=self.vector_store_service
        )

        call_kwargs = mock_vector_repo.upsert_vector_meta.call_args[1]
        self.assertEqual(len(call_kwargs['vectors_orm']), 0)

        qdrant_vectors = self.vector_store_service.upsert_vectors.call_args[1]['vector_points']
        self.assertEqual(len(qdrant_vectors), 0)

        self.cache_service.cache.delete_by_prefix.assert_called_once()

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    async def test_handle_vector_upsert_with_single_embedding(
            self, mock_vector_repo_class
    ):
        self.event.orm_embedding = [self.orm_embeddings[0]]
        mock_vector_repo = MagicMock()
        mock_vector_repo.upsert_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        await handle_vector_upsert(
            event=self.event,
            backend_connector=self.backend_connector,
            cache_service=self.cache_service,
            vector_store_service=self.vector_store_service
        )

        call_kwargs = mock_vector_repo.upsert_vector_meta.call_args[1]
        self.assertEqual(len(call_kwargs['vectors_orm']), 1)

        qdrant_vectors = self.vector_store_service.upsert_vectors.call_args[1]['vector_points']
        self.assertEqual(len(qdrant_vectors), 1)

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    @patch('vector_service.api.handlers.handle_upsert.logger')
    async def test_handle_vector_upsert_metadata_upsert_fails(
            self, mock_logger, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        error_msg = 'Database constraint violation'
        mock_vector_repo.upsert_vector_meta = AsyncMock(
            side_effect=VectorUpsertFailed(error_msg)
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        with self.assertRaises(VectorUpsertFailed):
            await handle_vector_upsert(
                event=self.event,
                backend_connector=self.backend_connector,
                cache_service=self.cache_service,
                vector_store_service=self.vector_store_service
            )

        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        self.assertIn('Upsert vector metadata failed with DB error', error_call[0][0])
        self.assertTrue(error_call[1]['exc_info'])
        self.assertEqual(error_call[1]['extra']['org_id'], self.organization_id)
        self.assertEqual(error_call[1]['extra']['user_id'], self.user_id)

        self.cache_service.cache.delete_by_prefix.assert_not_called()

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    @patch('vector_service.api.handlers.handle_upsert.logger')
    async def test_handle_vector_upsert_vector_store_upsert_fails(
            self, mock_logger, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.upsert_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        error_msg = 'Qdrant collection not found'
        self.vector_store_service.upsert_vectors = AsyncMock(
            side_effect=UpsertVectorDBFailed(error_msg)
        )

        with self.assertRaises(UpsertVectorDBFailed):
            await handle_vector_upsert(
                event=self.event,
                backend_connector=self.backend_connector,
                cache_service=self.cache_service,
                vector_store_service=self.vector_store_service
            )

        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        self.assertIn('Upsert vector to vector DB failed with client error', error_call[0][0])
        self.assertTrue(error_call[1]['exc_info'])

        self.cache_service.cache.delete_by_prefix.assert_not_called()

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    @patch('vector_service.api.handlers.handle_upsert.logger')
    async def test_handle_vector_upsert_unexpected_error(
            self, mock_logger, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.upsert_vector_meta = AsyncMock(
            side_effect=RuntimeError('Unexpected network error')
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        with self.assertRaises(RuntimeError):
            await handle_vector_upsert(
                event=self.event,
                backend_connector=self.backend_connector,
                cache_service=self.cache_service,
                vector_store_service=self.vector_store_service
            )

        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        self.assertIn('Unexpected error by handling upsert vectors', error_call[0][0])
        self.assertTrue(error_call[1]['exc_info'])

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    @patch('vector_service.api.handlers.handle_upsert.logger')
    async def test_handle_vector_upsert_cache_deletion_fails(
            self, mock_logger, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.upsert_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        self.cache_service.cache.delete_by_prefix = AsyncMock(
            side_effect=Exception('Redis connection timeout')
        )

        with self.assertRaises(Exception):
            await handle_vector_upsert(
                event=self.event,
                backend_connector=self.backend_connector,
                cache_service=self.cache_service,
                vector_store_service=self.vector_store_service
            )

        mock_vector_repo.upsert_vector_meta.assert_called_once()
        self.vector_store_service.upsert_vectors.assert_called_once()

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    async def test_handle_vector_upsert_concurrent_operations(
            self, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()

        call_order = []

        async def track_meta_upsert(*args, **kwargs):
            call_order.append('meta_start')
            await asyncio.sleep(0.1)
            call_order.append('meta_end')

        async def track_vector_upsert(*args, **kwargs):
            call_order.append('vector_start')
            await asyncio.sleep(0.1)
            call_order.append('vector_end')

        mock_vector_repo.upsert_vector_meta = AsyncMock(side_effect=track_meta_upsert)
        self.vector_store_service.upsert_vectors = AsyncMock(
            side_effect=track_vector_upsert
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        await handle_vector_upsert(
            event=self.event,
            backend_connector=self.backend_connector,
            cache_service=self.cache_service,
            vector_store_service=self.vector_store_service
        )

        self.assertIn('meta_start', call_order)
        self.assertIn('vector_start', call_order)
        meta_start_idx = call_order.index('meta_start')
        vector_start_idx = call_order.index('vector_start')
        meta_end_idx = call_order.index('meta_end')
        vector_end_idx = call_order.index('vector_end')

        self.assertTrue(
            meta_start_idx < meta_end_idx and
            vector_start_idx < vector_end_idx
        )

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    @patch('vector_service.api.handlers.handle_upsert.uuid.uuid4')
    async def test_handle_vector_upsert_unique_vector_ids(
            self, mock_uuid4, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.upsert_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        mock_uuids = [uuid4(), uuid4(), uuid4()]
        mock_uuid4.side_effect = mock_uuids

        self.event.orm_embedding.append(
            MockORMEmbedding(
                datastore_id=self.datastore_id,
                schema_name='public',
                table_name='products',
                table_meta=MockTableMeta(['id', 'name'], 'Products'),
                embedding=[1.1, 1.2, 1.3, 1.4, 1.5]
            )
        )

        await handle_vector_upsert(
            event=self.event,
            backend_connector=self.backend_connector,
            cache_service=self.cache_service,
            vector_store_service=self.vector_store_service
        )

        pg_vectors = mock_vector_repo.upsert_vector_meta.call_args[1]['vectors_orm']
        qdrant_vectors = self.vector_store_service.upsert_vectors.call_args[1]['vector_points']

        self.assertEqual(len(pg_vectors), 3)
        self.assertEqual(len(qdrant_vectors), 3)

        for i, (pg_vec, qdrant_vec) in enumerate(zip(pg_vectors, qdrant_vectors)):
            self.assertEqual(pg_vec.qdrant_vector_id, mock_uuids[i])
            self.assertEqual(qdrant_vec.id, mock_uuids[i])
            self.assertEqual(pg_vec.qdrant_vector_id, qdrant_vec.id)

    @patch('vector_service.api.handlers.handle_upsert.VectorRepository')
    async def test_handle_vector_upsert_table_meta_serialization(
            self, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.upsert_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        await handle_vector_upsert(
            event=self.event,
            backend_connector=self.backend_connector,
            cache_service=self.cache_service,
            vector_store_service=self.vector_store_service
        )

        pg_vectors = mock_vector_repo.upsert_vector_meta.call_args[1]['vectors_orm']

        self.assertIn("'columns'", pg_vectors[0].table_meta)
        self.assertIn("'description'", pg_vectors[0].table_meta)
        self.assertIn('Users table', pg_vectors[0].table_meta)
        self.assertIn('Orders table', pg_vectors[1].table_meta)
