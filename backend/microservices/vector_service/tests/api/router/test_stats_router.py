import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from svc_vector_contracts.models import VectorStatsResponse
from vector_service.api.router.stats_router import router
from vector_service.database.exceptions import VectorCountGetFailed


class MockUserIdentity:
    def __init__(self, organization_id, user_id):
        self.organization_id = organization_id
        self.user_id = user_id


class TestGetStatsEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)

        self.mock_backend_connector = MagicMock()
        self.mock_cache_service = MagicMock()
        self.app.state.backend_connector = self.mock_backend_connector
        self.app.state.cache_service = self.mock_cache_service

        self.client = TestClient(self.app)

        self.organization_id = uuid4()
        self.user_id = uuid4()

        self.user_identity = MockUserIdentity(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

    def _get_endpoint_url(self, org_id=None, user_id=None):
        org_id = org_id or self.organization_id
        user_id = user_id or self.user_id
        return f'/v1/vector/organizations/{org_id}/users/{user_id}/stats'

    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_success_no_cache(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)
        self.mock_cache_service.set_stats = AsyncMock()

        vector_count = 42
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(return_value=vector_count)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('vector_count', data)
        self.assertEqual(data['vector_count'], vector_count)

        mock_vector_repo.get_vector_count.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.mock_cache_service.set_stats.assert_called_once()

    @patch('vector_service.api.router.stats_router.get_current_identity')
    def test_get_stats_success_from_cache(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        cached_response = VectorStatsResponse(vector_count=100)
        self.mock_cache_service.get_stats = AsyncMock(return_value=cached_response)
        self.mock_cache_service.set_stats = AsyncMock()

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['vector_count'], 100)

        self.mock_cache_service.get_stats.assert_called_once_with(
            user_identity=self.user_identity
        )

        self.mock_cache_service.set_stats.assert_not_called()

    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_with_zero_count(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)
        self.mock_cache_service.set_stats = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(return_value=0)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['vector_count'], 0)

        self.mock_cache_service.set_stats.assert_called_once()

    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_with_large_count(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)
        self.mock_cache_service.set_stats = AsyncMock()

        large_count = 1_000_000
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(return_value=large_count)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['vector_count'], large_count)

    @patch('vector_service.api.router.stats_router.logger')
    @patch('vector_service.api.router.stats_router.get_current_identity')
    def test_get_stats_forbidden_wrong_organization(
            self,
            mock_get_identity,
            mock_logger
    ):
        wrong_org_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.get(self._get_endpoint_url(org_id=wrong_org_id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': {'message': 'Forbidden'}})

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Forbidden request', log_call[0][0])
        self.assertEqual(log_call[1]['extra']['org_id'], wrong_org_id)

    @patch('vector_service.api.router.stats_router.logger')
    @patch('vector_service.api.router.stats_router.get_current_identity')
    def test_get_stats_forbidden_wrong_user(
            self,
            mock_get_identity,
            mock_logger
    ):
        wrong_user_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.get(self._get_endpoint_url(user_id=wrong_user_id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': {'message': 'Forbidden'}})

    @patch('vector_service.api.router.stats_router.get_current_identity')
    def test_get_stats_forbidden_both_wrong(self, mock_get_identity):
        wrong_org_id = uuid4()
        wrong_user_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.get(
            self._get_endpoint_url(org_id=wrong_org_id, user_id=wrong_user_id)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('vector_service.api.router.stats_router.logger')
    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_database_error(
            self,
            mock_vector_repo_class,
            mock_get_identity,
            mock_logger
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)

        error_msg = 'Database connection timeout'
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(
            side_effect=VectorCountGetFailed(error_msg)
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

        response_data = response.json()
        self.assertIn('Database error', response_data['detail']['message'])
        self.assertIn(error_msg, response_data['detail']['message'])

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Get vector stats failed with DB error', log_call[0][0])
        self.assertTrue(log_call[1]['exc_info'])

        self.mock_cache_service.set_stats.assert_not_called()

    @patch('vector_service.api.router.stats_router.logger')
    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_unexpected_error(
            self,
            mock_vector_repo_class,
            mock_get_identity,
            mock_logger
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)

        error_msg = 'Unexpected network error'
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(
            side_effect=RuntimeError(error_msg)
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = response.json()
        self.assertIn('Unexpected error', response_data['detail']['message'])
        self.assertIn(error_msg, response_data['detail']['message'])

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Unexpected get vector stats error', log_call[0][0])
        self.assertTrue(log_call[1]['exc_info'])

    def test_get_stats_invalid_uuid_in_path_org(self):
        response = self.client.get(
            f'/v1/vector/organizations/invalid-uuid/users/{self.user_id}/stats'
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_get_stats_invalid_uuid_in_path_user(self):
        response = self.client.get(
            f'/v1/vector/organizations/{self.organization_id}/users/invalid-uuid/stats'
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch('vector_service.api.router.stats_router.get_current_identity')
    def test_get_stats_cache_get_error(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(
            side_effect=Exception('Redis connection error')
        )

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_cache_set_error(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)
        self.mock_cache_service.set_stats = AsyncMock(
            side_effect=Exception('Redis write error')
        )

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(return_value=42)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_response_structure(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)
        self.mock_cache_service.set_stats = AsyncMock()

        vector_count = 123
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(return_value=vector_count)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('vector_count', data)
        self.assertIsInstance(data['vector_count'], int)

    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_response_content_type(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)
        self.mock_cache_service.set_stats = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(return_value=50)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/json', response.headers['content-type'])

    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_multiple_calls_same_user(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)
        self.mock_cache_service.set_stats = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(return_value=75)
        mock_vector_repo_class.return_value = mock_vector_repo

        response1 = self.client.get(self._get_endpoint_url())
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.json()['vector_count'], 75)

        response2 = self.client.get(self._get_endpoint_url())
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.json()['vector_count'], 75)

        self.assertEqual(mock_vector_repo.get_vector_count.call_count, 2)

    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_different_users(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        user1_identity = MockUserIdentity(
            organization_id=self.organization_id,
            user_id=self.user_id
        )
        mock_get_identity.return_value = user1_identity

        self.mock_cache_service.get_stats = AsyncMock(return_value=None)
        self.mock_cache_service.set_stats = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(return_value=100)
        mock_vector_repo_class.return_value = mock_vector_repo

        response1 = self.client.get(self._get_endpoint_url())
        self.assertEqual(response1.json()['vector_count'], 100)

        user2_id = uuid4()
        user2_identity = MockUserIdentity(
            organization_id=self.organization_id,
            user_id=user2_id
        )
        mock_get_identity.return_value = user2_identity

        mock_vector_repo.get_vector_count = AsyncMock(return_value=200)

        response2 = self.client.get(
            self._get_endpoint_url(user_id=user2_id)
        )
        self.assertEqual(response2.json()['vector_count'], 200)

    @patch('vector_service.api.router.stats_router.get_current_identity')
    @patch('vector_service.api.router.stats_router.VectorRepository')
    def test_get_stats_caching_behavior(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        cached_response = VectorStatsResponse(vector_count=999)
        self.mock_cache_service.get_stats = AsyncMock(return_value=cached_response)

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vector_count = AsyncMock(return_value=100)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['vector_count'], 999)

        mock_vector_repo.get_vector_count.assert_not_called()
