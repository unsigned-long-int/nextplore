import json
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, call

from fastapi import HTTPException

from api.router.get_vector_metas_router import get_vector_metas
from database.exceptions import VectorGetFailed


def make_payload(vector_ids=None):
    return types.SimpleNamespace(
        vector_ids=[1, 2, 3] if vector_ids is None else vector_ids
    )


def make_identity(org_id=111, user_id=222):
    return types.SimpleNamespace(organization_id=org_id, user_id=user_id)


def make_vector_meta(integration_id, schema_name, table_name, table_meta_dict):
    return types.SimpleNamespace(
        integration_id=integration_id,
        schema_name=schema_name,
        table_name=table_name,
        table_meta=json.dumps(table_meta_dict),
    )


class TestGetVectorMetas(unittest.IsolatedAsyncioTestCase):
    @patch('api.router.get_vector_metas_router.get_current_identity')
    @patch('api.router.get_vector_metas_router.VectorRepository')
    @patch('api.router.get_vector_metas_router.VectorMetaResponse')
    async def test_cache_hit_returns_cached_directly(
        self, mock_resp_cls, mock_repo_cls, mock_get_id
    ):
        user_identity = make_identity()
        mock_get_id.return_value = user_identity

        payload = make_payload()
        cached_response = [MagicMock(name='CachedVectorMetaResponse')]

        cache_service = MagicMock()
        cache_service.get_vector_metas = AsyncMock(return_value=cached_response)
        cache_service.set_vector_metas = AsyncMock()

        connector = MagicMock(name='DatabaseBackendConnector')

        result = await get_vector_metas(
            payload,
            connector=connector,
            cache_service=cache_service,
        )

        self.assertIs(result, cached_response)

        cache_service.get_vector_metas.assert_awaited_once_with(
            user_identity=user_identity, request=payload
        )
        mock_repo_cls.assert_not_called()
        mock_resp_cls.assert_not_called()
        cache_service.set_vector_metas.assert_not_awaited()

    @patch('api.router.get_vector_metas_router.get_current_identity')
    @patch('api.router.get_vector_metas_router.VectorRepository')
    @patch('api.router.get_vector_metas_router.VectorMetaResponse')
    async def test_cache_miss_queries_repo_builds_response_and_sets_cache(
        self, mock_resp_cls, mock_repo_cls, mock_get_id
    ):
        user_identity = make_identity(org_id=9001, user_id=42)
        mock_get_id.return_value = user_identity
        payload = make_payload(vector_ids=[101, 102])

        cache_service = MagicMock()
        cache_service.get_vector_metas = AsyncMock(return_value=None)
        cache_service.set_vector_metas = AsyncMock()

        repo_instance = MagicMock(name='VectorRepositoryInstance')
        mock_repo_cls.return_value = repo_instance

        vm1 = make_vector_meta('int-A', 'schema1', 'table1', {'a': 1})
        vm2 = make_vector_meta('int-B', 'schema2', 'table2', {'b': 2})
        repo_instance.get_vectors = AsyncMock(return_value=[vm1, vm2])

        r1 = MagicMock(name='VectorMetaResponse#1')
        r2 = MagicMock(name='VectorMetaResponse#2')
        mock_resp_cls.side_effect = [r1, r2]

        connector = MagicMock(name='DatabaseBackendConnector')

        result = await get_vector_metas(
            payload,
            connector=connector,
            cache_service=cache_service,
        )

        mock_repo_cls.assert_called_once_with(connector)
        repo_instance.get_vectors.assert_awaited_once_with(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            vector_ids=payload.vector_ids,
        )

        mock_resp_cls.assert_has_calls(
            [
                call(
                    integration_id='int-A',
                    schema_name='schema1',
                    table_name='table1',
                    table_meta={'a': 1},
                ),
                call(
                    integration_id='int-B',
                    schema_name='schema2',
                    table_name='table2',
                    table_meta={'b': 2},
                ),
            ],
            any_order=False,
        )

        self.assertEqual(result, [r1, r2])

        cache_service.set_vector_metas.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
            response=[r1, r2],
        )

    @patch('api.router.get_vector_metas_router.get_current_identity')
    @patch('api.router.get_vector_metas_router.VectorRepository')
    @patch('api.router.get_vector_metas_router.VectorMetaResponse')
    async def test_empty_db_result_returns_empty_and_caches(
        self, mock_resp_cls, mock_repo_cls, mock_get_id
    ):
        user_identity = make_identity()
        mock_get_id.return_value = user_identity
        payload = make_payload(vector_ids=[])

        cache_service = MagicMock()
        cache_service.get_vector_metas = AsyncMock(return_value=None)
        cache_service.set_vector_metas = AsyncMock()

        repo_instance = MagicMock()
        mock_repo_cls.return_value = repo_instance
        repo_instance.get_vectors = AsyncMock(return_value=[])

        connector = MagicMock()

        result = await get_vector_metas(
            payload,
            connector=connector,
            cache_service=cache_service,
        )

        mock_resp_cls.assert_not_called()
        self.assertEqual(result, [])
        cache_service.set_vector_metas.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
            response=[],
        )

    @patch('api.router.get_vector_metas_router.get_current_identity')
    @patch('api.router.get_vector_metas_router.VectorRepository')
    async def test_vectorgetfailed_maps_to_424(self, mock_repo_cls, mock_get_id):
        user_identity = make_identity()
        mock_get_id.return_value = user_identity
        payload = make_payload([9, 8, 7])

        cache_service = MagicMock()
        cache_service.get_vector_metas = AsyncMock(return_value=None)

        repo_instance = MagicMock()
        mock_repo_cls.return_value = repo_instance
        repo_instance.get_vectors = AsyncMock(side_effect=VectorGetFailed('db error'))

        connector = MagicMock()

        with self.assertRaises(HTTPException) as ctx:
            await get_vector_metas(
                payload,
                connector=connector,
                cache_service=cache_service,
            )

        self.assertEqual(ctx.exception.status_code, 424)
        self.assertIn('Database error:', ctx.exception.detail.get('message', ''))

    @patch('api.router.get_vector_metas_router.get_current_identity')
    @patch('api.router.get_vector_metas_router.VectorRepository')
    async def test_unexpected_exception_maps_to_500(self, mock_repo_cls, mock_get_id):
        user_identity = make_identity()
        mock_get_id.return_value = user_identity
        payload = make_payload([4, 5, 6])

        cache_service = MagicMock()
        cache_service.get_vector_metas = AsyncMock(return_value=None)

        repo_instance = MagicMock()
        mock_repo_cls.return_value = repo_instance
        repo_instance.get_vectors = AsyncMock(side_effect=RuntimeError('boom'))

        connector = MagicMock()

        with self.assertRaises(HTTPException) as ctx:
            await get_vector_metas(
                payload,
                connector=connector,
                cache_service=cache_service,
            )

        self.assertEqual(ctx.exception.status_code, 500)
        self.assertIn('Unexpected error:', ctx.exception.detail.get('message', ''))
