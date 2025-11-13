import types
import uuid
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, call

from integration_service.api.handlers import handle_vector_upsert


def make_embedding(integration_id='int-1', schema='public', table='items', emb=None, meta_json={'k': 'v'}):
    class _Meta:
        def model_dump_json(self):
            return meta_json

    return types.SimpleNamespace(
        integration_id=integration_id,
        schema_name=schema,
        table_name=table,
        table_meta=_Meta(),
        embedding=emb if emb is not None else [0.1, 0.2, 0.3],
    )


def make_event(org_id=111, user_id=222, embeddings=None):
    return types.SimpleNamespace(
        organization_id=org_id,
        user_id=user_id,
        orm_embedding=embeddings if embeddings is not None else [
            make_embedding('int-1', 's1', 't1', [1.0, 1.1]),
            make_embedding('int-2', 's2', 't2', [2.0, 2.2]),
        ],
    )


class TestHandleVectorUpsert(unittest.IsolatedAsyncioTestCase):
    @patch('api.handlers.handle_upsert.VectorRepository')
    @patch('api.handlers.handle_upsert.VectorORM')
    @patch('api.handlers.handle_upsert.VectorPoint')
    @patch('api.handlers.handle_upsert.uuid')
    async def test_happy_path(self, mock_uuid, mock_vector_point, mock_vector_orm, mock_repo_ctor):
        u1 = uuid.UUID('11111111-1111-1111-1111-111111111111')
        u2 = uuid.UUID('22222222-2222-2222-2222-222222222222')
        mock_uuid.uuid4.side_effect = [u1, u2]

        event = make_event()
        connector = MagicMock(name='DatabaseBackendConnector')

        repo_instance = MagicMock(name='VectorRepositoryInstance')
        repo_instance.upsert_vector_meta = AsyncMock()
        mock_repo_ctor.return_value = repo_instance

        vm1, vm2 = MagicMock(name='VectorORM#1'), MagicMock(name='VectorORM#2')
        vp1, vp2 = MagicMock(name='VectorPoint#1'), MagicMock(name='VectorPoint#2')
        mock_vector_orm.side_effect = [vm1, vm2]
        mock_vector_point.side_effect = [vp1, vp2]

        cache_service = MagicMock()
        cache_service.cache = MagicMock()
        cache_service.cache.delete_by_prefix = AsyncMock()

        vector_store_service = MagicMock()
        vector_store_service.upsert_vectors = AsyncMock()

        await handle_vector_upsert(event, connector, cache_service, vector_store_service)

        e1, e2 = event.orm_embedding
        mock_vector_orm.assert_has_calls([
            call(
                user_id=event.user_id,
                organization_id=event.organization_id,
                qdrant_vector_id=u1,
                integration_id=e1.integration_id,
                schema_name=e1.schema_name,
                table_name=e1.table_name,
                table_meta=e1.table_meta.model_dump_json(),
            ),
            call(
                user_id=event.user_id,
                organization_id=event.organization_id,
                qdrant_vector_id=u2,
                integration_id=e2.integration_id,
                schema_name=e2.schema_name,
                table_name=e2.table_name,
                table_meta=e2.table_meta.model_dump_json(),
            ),
        ], any_order=False)

        mock_vector_point.assert_has_calls([
            call(
                id=u1,
                user_id=event.user_id,
                organization_id=event.organization_id,
                vector=e1.embedding,
            ),
            call(
                id=u2,
                user_id=event.user_id,
                organization_id=event.organization_id,
                vector=e2.embedding,
            ),
        ], any_order=False)

        mock_repo_ctor.assert_called_once_with(connector)
        repo_instance.upsert_vector_meta.assert_awaited_once_with(
            organization_id=event.organization_id,
            user_id=event.user_id,
            vectors_orm=[vm1, vm2],
        )
        vector_store_service.upsert_vectors.assert_awaited_once_with(
            vector_points=[vp1, vp2]
        )

        cache_service.cache.delete_by_prefix.assert_awaited_once_with(
            event.organization_id, event.user_id
        )

    @patch('api.handlers.handle_upsert.VectorRepository')
    @patch('api.handlers.handle_upsert.VectorORM')
    @patch('api.handlers.handle_upsert.VectorPoint')
    @patch('api.handlers.handle_upsert.uuid')
    async def test_empty_embeddings(self, mock_uuid, mock_vector_point, mock_vector_orm, mock_repo_ctor):
        event = make_event(embeddings=[])
        connector = MagicMock()

        repo_instance = MagicMock()
        repo_instance.upsert_vector_meta = AsyncMock()
        mock_repo_ctor.return_value = repo_instance

        cache_service = MagicMock()
        cache_service.cache = MagicMock()
        cache_service.cache.delete_by_prefix = AsyncMock()

        vector_store_service = MagicMock()
        vector_store_service.upsert_vectors = AsyncMock()

        await handle_vector_upsert(event, connector, cache_service, vector_store_service)

        mock_vector_orm.assert_not_called()
        mock_vector_point.assert_not_called()

        repo_instance.upsert_vector_meta.assert_awaited_once_with(
            organization_id=event.organization_id,
            user_id=event.user_id,
            vectors_orm=[],
        )
        vector_store_service.upsert_vectors.assert_awaited_once_with(
            vector_points=[]
        )
        cache_service.cache.delete_by_prefix.assert_awaited_once_with(
            event.organization_id, event.user_id
        )
