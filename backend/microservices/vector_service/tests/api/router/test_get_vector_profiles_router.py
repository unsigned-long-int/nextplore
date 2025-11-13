import json
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, call

from fastapi import HTTPException

from vector_service.api.router.profiles_router import get_vector_profiles
from integration_service.database import VectorProfilesGetFailed


def make_payload(integration_id='int-123'):
    return types.SimpleNamespace(integration_id=integration_id)


def make_identity(org_id=111, user_id=222):
    return types.SimpleNamespace(organization_id=org_id, user_id=user_id)


def make_vector_profile(integration_id, schema_name, table_name, table_meta_dict):
    return types.SimpleNamespace(
        integration_id=integration_id,
        schema_name=schema_name,
        table_name=table_name,
        table_meta=json.dumps(table_meta_dict),
    )


class TestGetVectorProfiles(unittest.IsolatedAsyncioTestCase):
    @patch('api.router.get_vector_profiles_router.get_current_identity')
    @patch('api.router.get_vector_profiles_router.VectorRepository')
    @patch('api.router.get_vector_profiles_router.VectorProfileResponse')
    async def test_cache_hit_returns_cached_immediately(
        self, mock_resp_cls, mock_repo_cls, mock_get_id
    ):
        user_identity = make_identity()
        mock_get_id.return_value = user_identity

        payload = make_payload()
        cached = [MagicMock(name='CachedVectorProfileResponse')]

        cache_service = MagicMock()
        cache_service.get_vector_profiles = AsyncMock(return_value=cached)
        cache_service.set_vector_profiles = AsyncMock()

        connector = MagicMock(name='DatabaseBackendConnector')

        result = await get_vector_profiles(
            payload,
            connector=connector,
            cache_service=cache_service,
        )

        self.assertIs(result, cached)

        cache_service.get_vector_profiles.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
        )
        mock_repo_cls.assert_not_called()
        mock_resp_cls.assert_not_called()
        cache_service.set_vector_profiles.assert_not_awaited()

    @patch('api.router.get_vector_profiles_router.get_current_identity')
    @patch('api.router.get_vector_profiles_router.VectorRepository')
    @patch('api.router.get_vector_profiles_router.VectorProfileResponse')
    async def test_cache_miss_queries_repo_builds_response_and_sets_cache(
        self, mock_resp_cls, mock_repo_cls, mock_get_id
    ):
        user_identity = make_identity(org_id=9001, user_id=77)
        mock_get_id.return_value = user_identity

        payload = make_payload(integration_id='int-XYZ')

        cache_service = MagicMock()
        cache_service.get_vector_profiles = AsyncMock(return_value=None)
        cache_service.set_vector_profiles = AsyncMock()

        repo_instance = MagicMock(name='VectorRepositoryInstance')
        mock_repo_cls.return_value = repo_instance

        vp1 = make_vector_profile('int-XYZ', 'schema_a', 'table_a', {'a': 1})
        vp2 = make_vector_profile('int-XYZ', 'schema_b', 'table_b', {'b': 2})
        repo_instance.get_vector_profiles = AsyncMock(return_value=[vp1, vp2])

        r1 = MagicMock(name='VectorProfileResponse#1')
        r2 = MagicMock(name='VectorProfileResponse#2')
        mock_resp_cls.side_effect = [r1, r2]

        connector = MagicMock(name='DatabaseBackendConnector')

        result = await get_vector_profiles(
            payload,
            connector=connector,
            cache_service=cache_service,
        )

        mock_repo_cls.assert_called_once_with(connector)
        repo_instance.get_vector_profiles.assert_awaited_once_with(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration_id=payload.integration_id,
        )

        mock_resp_cls.assert_has_calls(
            [
                call(
                    integration_id='int-XYZ',
                    schema_name='schema_a',
                    table_name='table_a',
                    table_meta={'a': 1},
                ),
                call(
                    integration_id='int-XYZ',
                    schema_name='schema_b',
                    table_name='table_b',
                    table_meta={'b': 2},
                ),
            ],
            any_order=False,
        )

        self.assertEqual(result, [r1, r2])
        cache_service.set_vector_profiles.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
            response=[r1, r2],
        )

    @patch('api.router.get_vector_profiles_router.get_current_identity')
    @patch('api.router.get_vector_profiles_router.VectorRepository')
    @patch('api.router.get_vector_profiles_router.VectorProfileResponse')
    async def test_empty_db_result_returns_empty_and_caches(
        self, mock_resp_cls, mock_repo_cls, mock_get_id
    ):
        mock_get_id.return_value = make_identity()

        payload = make_payload('int-empty')

        cache_service = MagicMock()
        cache_service.get_vector_profiles = AsyncMock(return_value=None)
        cache_service.set_vector_profiles = AsyncMock()

        repo_instance = MagicMock()
        mock_repo_cls.return_value = repo_instance
        repo_instance.get_vector_profiles = AsyncMock(return_value=[])

        connector = MagicMock()

        result = await get_vector_profiles(
            payload,
            connector=connector,
            cache_service=cache_service,
        )

        mock_resp_cls.assert_not_called()
        self.assertEqual(result, [])
        cache_service.set_vector_profiles.assert_awaited_once_with(
            user_identity=make_identity(),
            request=payload,
            response=[],
        )

    @patch('api.router.get_vector_profiles_router.get_current_identity')
    @patch('api.router.get_vector_profiles_router.VectorRepository')
    async def test_vectorprofilesgetfailed_maps_to_424(
        self, mock_repo_cls, mock_get_id
    ):
        mock_get_id.return_value = make_identity()
        payload = make_payload('int-err')

        cache_service = MagicMock()
        cache_service.get_vector_profiles = AsyncMock(return_value=None)

        repo_instance = MagicMock()
        mock_repo_cls.return_value = repo_instance
        repo_instance.get_vector_profiles = AsyncMock(
            side_effect=VectorProfilesGetFailed('DB said nope')
        )

        connector = MagicMock()

        with self.assertRaises(HTTPException) as ctx:
            await get_vector_profiles(
                payload,
                connector=connector,
                cache_service=cache_service,
            )

        self.assertEqual(ctx.exception.status_code, 424)
        self.assertIn('Database error:', ctx.exception.detail.get('message', ''))

    @patch('api.router.get_vector_profiles_router.get_current_identity')
    @patch('api.router.get_vector_profiles_router.VectorRepository')
    async def test_unexpected_exception_maps_to_500(
        self, mock_repo_cls, mock_get_id
    ):
        mock_get_id.return_value = make_identity()
        payload = make_payload('int-500')

        cache_service = MagicMock()
        cache_service.get_vector_profiles = AsyncMock(return_value=None)

        repo_instance = MagicMock()
        mock_repo_cls.return_value = repo_instance
        repo_instance.get_vector_profiles = AsyncMock(
            side_effect=RuntimeError('boom')
        )

        connector = MagicMock()

        with self.assertRaises(HTTPException) as ctx:
            await get_vector_profiles(
                payload,
                connector=connector,
                cache_service=cache_service,
            )

        self.assertEqual(ctx.exception.status_code, 500)
        self.assertIn('Unexpected error:', ctx.exception.detail.get('message', ''))
