import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from api.router.get_vector_stats_router import get_vector_stats


def make_payload(org_id=111, user_id=222):
    return types.SimpleNamespace(organization_id=org_id, user_id=user_id)


def make_identity(sub='user-abc'):
    return types.SimpleNamespace(sub=sub)


class TestGetVectorStats(unittest.IsolatedAsyncioTestCase):
    @patch('api.router.get_vector_stats_router.get_current_identity')
    @patch('api.router.get_vector_stats_router.VectorRepository')
    @patch('api.router.get_vector_stats_router.VectorStatsResponse')
    async def test_cache_hit_returns_cached_immediately(
        self, mock_resp_cls, mock_repo_cls, mock_get_id
    ):
        user_identity = make_identity()
        mock_get_id.return_value = user_identity

        payload = make_payload()
        cached = MagicMock(name='CachedVectorStatsResponse')

        cache_service = MagicMock()
        cache_service.get_vector_stats = AsyncMock(return_value=cached)
        cache_service.set_vector_stats = AsyncMock()

        connector = MagicMock(name='DatabaseBackendConnector')

        result = await get_vector_stats(
            payload,
            connector=connector,
            cache_service=cache_service,
        )

        self.assertIs(result, cached)

        cache_service.get_vector_stats.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
        )
        mock_repo_cls.assert_not_called()
        mock_resp_cls.assert_not_called()
        cache_service.set_vector_stats.assert_not_awaited()

    @patch('api.router.get_vector_stats_router.get_current_identity')
    @patch('api.router.get_vector_stats_router.VectorRepository')
    @patch('api.router.get_vector_stats_router.VectorStatsResponse')
    async def test_cache_miss_queries_repo_builds_response_and_sets_cache(
        self, mock_resp_cls, mock_repo_cls, mock_get_id
    ):
        user_identity = make_identity()
        mock_get_id.return_value = user_identity

        payload = make_payload(org_id=9001, user_id=77)

        cache_service = MagicMock()
        cache_service.get_vector_stats = AsyncMock(return_value=None)
        cache_service.set_vector_stats = AsyncMock()

        repo_instance = MagicMock(name='VectorRepositoryInstance')
        mock_repo_cls.return_value = repo_instance
        repo_instance.get_vector_count = AsyncMock(return_value=7)

        response_instance = MagicMock(name='VectorStatsResponseInstance')
        mock_resp_cls.return_value = response_instance

        connector = MagicMock(name='DatabaseBackendConnector')

        result = await get_vector_stats(
            payload,
            connector=connector,
            cache_service=cache_service,
        )

        mock_repo_cls.assert_called_once_with(connector)
        repo_instance.get_vector_count.assert_awaited_once_with(
            organization_id=payload.organization_id,
            user_id=payload.user_id,
        )

        mock_resp_cls.assert_called_once_with(vector_count=7)
        self.assertIs(result, response_instance)

        cache_service.set_vector_stats.assert_awaited_once_with(
            user_identity=user_identity,
            request=payload,
            response=response_instance,
        )
