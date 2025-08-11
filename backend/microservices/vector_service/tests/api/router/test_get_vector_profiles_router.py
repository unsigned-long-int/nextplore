import json
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, call

from api.router.get_vector_profiles_router import get_vector_profiles


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
    @patch('api.router.get_vector_profiles_router.vector_service_cache')
    @patch('api.router.get_vector_profiles_router.VectorRepository')
    @patch('api.router.get_vector_profiles_router.VectorProfileResponse')
    async def test_cache_hit_returns_cached_immediately(
        self, mock_resp_cls, mock_repo_cls, mock_cache, mock_get_id
    ):
        user_identity = make_identity()
        mock_get_id.return_value = user_identity

        payload = make_payload()
        cached = [MagicMock(name='CachedVectorProfileResponse')]
        mock_cache.get_vector_profiles = AsyncMock(return_value=cached)
        mock_cache.set_vector_profiles = AsyncMock()

        connector = MagicMock(name='DatabaseBackendConnector')

        result = await get_vector_profiles(payload, connector)

        self.assertIs(result, cached)
        mock_cache.get_vector_profiles.assert_awaited_once_with(
            user_identity=user_identity, request=payload
        )
        mock_repo_cls.assert_not_called()
        mock_resp_cls.assert_not_called()
        mock_cache.set_vector_profiles.assert_not_awaited()

    @patch('api.router.get_vector_profiles_router.get_current_identity')
    @patch('api.router.get_vector_profiles_router.vector_service_cache')
    @patch('api.router.get_vector_profiles_router.VectorRepository')
    @patch('api.router.get_vector_profiles_router.VectorProfileResponse')
    async def test_cache_miss_queries_repo_builds_response_and_sets_cache(
        self, mock_resp_cls, mock_repo_cls, mock_cache, mock_get_id
    ):
        user_identity = make_identity(org_id=9001, user_id=77)
        mock_get_id.return_value = user_identity

        payload = make_payload(integration_id='int-XYZ')

        mock_cache.get_vector_profiles = AsyncMock(return_value=None)
        mock_cache.set_vector_profiles = AsyncMock()

        repo_instance = MagicMock(name='VectorRepositoryInstance')
        mock_repo_cls.return_value = repo_instance

        vp1 = make_vector_profile('int-XYZ', 'schema_a', 'table_a', {'a': 1})
        vp2 = make_vector_profile('int-XYZ', 'schema_b', 'table_b', {'b': 2})
        repo_instance.get_vector_profiles = AsyncMock(return_value=[vp1, vp2])

        r1 = MagicMock(name='VectorProfileResponse#1')
        r2 = MagicMock(name='VectorProfileResponse#2')
        mock_resp_cls.side_effect = [r1, r2]

        connector = MagicMock(name='DatabaseBackendConnector')

        result = await get_vector_profiles(payload, connector)

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
        mock_cache.set_vector_profiles.assert_awaited_once_with(
            user_identity=user_identity, request=payload, response=[r1, r2]
        )

