import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from kafka_messaging.events.integration_service import DataStoreDeleted

from vector_service.api.handlers import handle_vector_delete
from vector_service.database.exceptions import VectorDeleteFailed
from vector_service.services.vector_store_service.exceptions import DeleteVectorDBFailed


class TestHandleVectorDelete(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.datastore_id = uuid4()

        self.event = DataStoreDeleted(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
        )

        self.backend_connector = MagicMock()
        self.cache_service = MagicMock()
        self.cache_service.cache = MagicMock()
        self.cache_service.cache.delete_by_prefix = AsyncMock()
        self.vector_store_service = MagicMock()
        self.vector_store_service.delete_vectors = AsyncMock()

        self.qdrant_vector_ids = [uuid4(), uuid4(), uuid4()]
        self.expected_vector_ids = [str(v_id) for v_id in self.qdrant_vector_ids]

    @patch("vector_service.api.handlers.handle_delete.VectorRepository")
    async def test_handle_vector_delete_success(self, mock_vector_repo_class):
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_qdrant_vector_ids = AsyncMock(
            return_value=self.qdrant_vector_ids
        )
        mock_vector_repo.delete_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        await handle_vector_delete(
            event=self.event,
            backend_connector=self.backend_connector,
            cache_service=self.cache_service,
            vector_store_service=self.vector_store_service,
        )

        mock_vector_repo_class.assert_called_once_with(self.backend_connector)

        mock_vector_repo.get_qdrant_vector_ids.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
        )

        mock_vector_repo.delete_vector_meta.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_id=self.datastore_id,
        )

        self.vector_store_service.delete_vectors.assert_called_once_with(
            vector_ids=self.expected_vector_ids,
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
        )

        self.cache_service.cache.delete_by_prefix.assert_called_once_with(
            self.organization_id, self.user_id
        )

    @patch("vector_service.api.handlers.handle_delete.VectorRepository")
    async def test_handle_vector_delete_with_empty_vector_ids(
        self, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_qdrant_vector_ids = AsyncMock(return_value=[])
        mock_vector_repo.delete_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        await handle_vector_delete(
            event=self.event,
            backend_connector=self.backend_connector,
            cache_service=self.cache_service,
            vector_store_service=self.vector_store_service,
        )

        self.vector_store_service.delete_vectors.assert_called_once_with(
            vector_ids=[],
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
        )

        self.cache_service.cache.delete_by_prefix.assert_called_once()

    @patch("vector_service.api.handlers.handle_delete.VectorRepository")
    @patch("vector_service.api.handlers.handle_delete.logger")
    async def test_handle_vector_delete_metadata_deletion_fails(
        self, mock_logger, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_qdrant_vector_ids = AsyncMock(
            return_value=self.qdrant_vector_ids
        )
        error_msg = "Database connection failed"
        mock_vector_repo.delete_vector_meta = AsyncMock(
            side_effect=VectorDeleteFailed(error_msg)
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        with self.assertRaises(VectorDeleteFailed):
            await handle_vector_delete(
                event=self.event,
                backend_connector=self.backend_connector,
                cache_service=self.cache_service,
                vector_store_service=self.vector_store_service,
            )

        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        self.assertIn("Delete vector metadata failed with DB error", error_call[0][0])
        self.assertTrue(error_call[1]["exc_info"])
        self.assertEqual(error_call[1]["extra"]["org_id"], self.organization_id)
        self.assertEqual(error_call[1]["extra"]["user_id"], self.user_id)

        self.cache_service.cache.delete_by_prefix.assert_not_called()

    @patch("vector_service.api.handlers.handle_delete.VectorRepository")
    @patch("vector_service.api.handlers.handle_delete.logger")
    async def test_handle_vector_delete_vector_store_deletion_fails(
        self, mock_logger, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_qdrant_vector_ids = AsyncMock(
            return_value=self.qdrant_vector_ids
        )
        mock_vector_repo.delete_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        error_msg = "Qdrant client error"
        self.vector_store_service.delete_vectors = AsyncMock(
            side_effect=DeleteVectorDBFailed(error_msg)
        )

        with self.assertRaises(DeleteVectorDBFailed):
            await handle_vector_delete(
                event=self.event,
                backend_connector=self.backend_connector,
                cache_service=self.cache_service,
                vector_store_service=self.vector_store_service,
            )
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        self.assertIn(
            "Delete vector from vector DB failed with client error", error_call[0][0]
        )
        self.assertTrue(error_call[1]["exc_info"])

        self.cache_service.cache.delete_by_prefix.assert_not_called()

    @patch("vector_service.api.handlers.handle_delete.VectorRepository")
    @patch("vector_service.api.handlers.handle_delete.logger")
    async def test_handle_vector_delete_unexpected_error(
        self, mock_logger, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_qdrant_vector_ids = AsyncMock(
            return_value=self.qdrant_vector_ids
        )
        mock_vector_repo.delete_vector_meta = AsyncMock(
            side_effect=RuntimeError("Unexpected error")
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        with self.assertRaises(RuntimeError):
            await handle_vector_delete(
                event=self.event,
                backend_connector=self.backend_connector,
                cache_service=self.cache_service,
                vector_store_service=self.vector_store_service,
            )

        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        self.assertIn("Unexpected error by handling delete vectors", error_call[0][0])
        self.assertTrue(error_call[1]["exc_info"])

    @patch("vector_service.api.handlers.handle_delete.VectorRepository")
    @patch("vector_service.api.handlers.handle_delete.logger")
    async def test_handle_vector_delete_cache_deletion_fails(
        self, mock_logger, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_qdrant_vector_ids = AsyncMock(
            return_value=self.qdrant_vector_ids
        )
        mock_vector_repo.delete_vector_meta = AsyncMock()
        mock_vector_repo_class.return_value = mock_vector_repo

        self.cache_service.cache.delete_by_prefix = AsyncMock(
            side_effect=Exception("Redis connection error")
        )

        with self.assertRaises(Exception):
            await handle_vector_delete(
                event=self.event,
                backend_connector=self.backend_connector,
                cache_service=self.cache_service,
                vector_store_service=self.vector_store_service,
            )

        mock_vector_repo.delete_vector_meta.assert_called_once()
        self.vector_store_service.delete_vectors.assert_called_once()

    @patch("vector_service.api.handlers.handle_delete.VectorRepository")
    async def test_handle_vector_delete_concurrent_operations(
        self, mock_vector_repo_class
    ):
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_qdrant_vector_ids = AsyncMock(
            return_value=self.qdrant_vector_ids
        )

        call_order = []

        async def track_meta_delete(*args, **kwargs):
            call_order.append("meta_start")
            await asyncio.sleep(0.1)
            call_order.append("meta_end")

        async def track_vector_delete(*args, **kwargs):
            call_order.append("vector_start")
            await asyncio.sleep(0.1)
            call_order.append("vector_end")

        mock_vector_repo.delete_vector_meta = AsyncMock(side_effect=track_meta_delete)
        self.vector_store_service.delete_vectors = AsyncMock(
            side_effect=track_vector_delete
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        await handle_vector_delete(
            event=self.event,
            backend_connector=self.backend_connector,
            cache_service=self.cache_service,
            vector_store_service=self.vector_store_service,
        )

        self.assertIn("meta_start", call_order)
        self.assertIn("vector_start", call_order)
        meta_start_idx = call_order.index("meta_start")
        vector_start_idx = call_order.index("vector_start")
        meta_end_idx = call_order.index("meta_end")
        vector_end_idx = call_order.index("vector_end")

        self.assertTrue(
            meta_start_idx < meta_end_idx and vector_start_idx < vector_end_idx
        )
