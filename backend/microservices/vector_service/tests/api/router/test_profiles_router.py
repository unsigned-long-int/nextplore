import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from svc_vector_contracts.models import VectorProfileResponse
from vector_service.api.router.profiles_router import router
from vector_service.database.exceptions import VectorProfilesGetFailed


class MockUserIdentity:
    def __init__(self, organization_id, user_id):
        self.organization_id = organization_id
        self.user_id = user_id


class MockVectorProfile:
    def __init__(self, integration_id, schema_name, table_name, table_meta):
        self.integration_id = integration_id
        self.schema_name = schema_name
        self.table_name = table_name
        self.table_meta = table_meta


class TestGetProfilesEndpoint(unittest.TestCase):
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
        self.integration_id = uuid4()

        self.user_identity = MockUserIdentity(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.table_meta_1 = '{"columns": ["id", "name", "email"], "description": "Users table"}'
        self.table_meta_2 = '{"columns": ["id", "user_id", "amount"], "description": "Orders table"}'
        self.table_meta_3 = '{"columns": ["id", "product_name", "price"], "description": "Products table"}'

        self.mock_vector_profiles = [
            MockVectorProfile(
                integration_id=self.integration_id,
                schema_name='public',
                table_name='users',
                table_meta=self.table_meta_1
            ),
            MockVectorProfile(
                integration_id=self.integration_id,
                schema_name='public',
                table_name='orders',
                table_meta=self.table_meta_2
            ),
            MockVectorProfile(
                integration_id=self.integration_id,
                schema_name='analytics',
                table_name='products',
                table_meta=self.table_meta_3
            )
        ]

    def _get_endpoint_url(self, org_id=None, user_id=None, integration_id=None):
        org_id = org_id or self.organization_id
        user_id = user_id or self.user_id
        integration_id = integration_id or self.integration_id
        return f'/v1/vector/organizations/{org_id}/users/{user_id}/integrations/{integration_id}/vectors/profiles'

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_success_no_cache(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_profiles = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(return_value=self.mock_vector_profiles)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 3)

        self.assertEqual(data[0]['integration_id'], str(self.integration_id))
        self.assertEqual(data[0]['schema_name'], 'public')
        self.assertEqual(data[0]['table_name'], 'users')
        self.assertEqual(data[0]['table_meta'], self.table_meta_1)

        self.assertEqual(data[1]['table_name'], 'orders')
        self.assertEqual(data[1]['table_meta'], self.table_meta_2)

        self.assertEqual(data[2]['schema_name'], 'analytics')
        self.assertEqual(data[2]['table_name'], 'products')
        self.assertEqual(data[2]['table_meta'], self.table_meta_3)

        mock_vector_repo.get_profiles.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            integration_id=self.integration_id
        )

        self.mock_cache_service.set_vector_profiles.assert_called_once()

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    def test_get_profiles_success_from_cache(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        cached_response = [
            VectorProfileResponse(
                integration_id=self.integration_id,
                schema_name='public',
                table_name='users',
                table_meta=self.table_meta_1
            ),
            VectorProfileResponse(
                integration_id=self.integration_id,
                schema_name='public',
                table_name='orders',
                table_meta=self.table_meta_2
            )
        ]

        self.mock_cache_service.get_vector_profiles = AsyncMock(
            return_value=cached_response
        )
        self.mock_cache_service.set_vector_profiles = AsyncMock()

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['table_name'], 'users')
        self.assertEqual(data[1]['table_name'], 'orders')

        self.mock_cache_service.get_vector_profiles.assert_called_once_with(
            user_identity=self.user_identity,
            integration_id=self.integration_id
        )

        self.mock_cache_service.set_vector_profiles.assert_not_called()

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_with_empty_results(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_profiles = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(return_value=[])
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

        self.mock_cache_service.set_vector_profiles.assert_called_once()

    @patch('vector_service.api.router.profiles_router.logger')
    @patch('vector_service.api.router.profiles_router.get_current_identity')
    def test_get_profiles_forbidden_wrong_organization(
            self,
            mock_get_identity,
            mock_logger
    ):
        wrong_org_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.get(
            self._get_endpoint_url(org_id=wrong_org_id)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': {'message': 'Forbidden'}})

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Forbidden request', log_call[0][0])
        self.assertEqual(log_call[1]['extra']['org_id'], wrong_org_id)

    @patch('vector_service.api.router.profiles_router.logger')
    @patch('vector_service.api.router.profiles_router.get_current_identity')
    def test_get_profiles_forbidden_wrong_user(
            self,
            mock_get_identity,
            mock_logger
    ):
        wrong_user_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.get(
            self._get_endpoint_url(user_id=wrong_user_id)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': {'message': 'Forbidden'}})

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    def test_get_profiles_forbidden_both_wrong(self, mock_get_identity):
        wrong_org_id = uuid4()
        wrong_user_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.get(
            self._get_endpoint_url(org_id=wrong_org_id, user_id=wrong_user_id)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('vector_service.api.router.profiles_router.logger')
    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_database_error(
            self,
            mock_vector_repo_class,
            mock_get_identity,
            mock_logger
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)

        error_msg = 'Database connection timeout'
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(
            side_effect=VectorProfilesGetFailed(error_msg)
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

        response_data = response.json()
        self.assertIn('Database error', response_data['detail']['message'])
        self.assertIn(error_msg, response_data['detail']['message'])

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Get vector profiles failed with DB error', log_call[0][0])
        self.assertTrue(log_call[1]['exc_info'])

        self.mock_cache_service.set_vector_profiles.assert_not_called()

    @patch('vector_service.api.router.profiles_router.logger')
    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_unexpected_error(
            self,
            mock_vector_repo_class,
            mock_get_identity,
            mock_logger
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)

        error_msg = 'Unexpected network error'
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(
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
        self.assertIn('Unexpected get vector profiles error', log_call[0][0])
        self.assertTrue(log_call[1]['exc_info'])

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_with_single_profile(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_profiles = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(
            return_value=[self.mock_vector_profiles[0]]
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['table_name'], 'users')

    def test_get_profiles_invalid_uuid_in_path_org(self):
        response = self.client.get(
            f'/v1/vector/organizations/invalid-uuid/users/{self.user_id}/integrations/{self.integration_id}/vectors/profiles'
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_get_profiles_invalid_uuid_in_path_user(self):
        response = self.client.get(
            f'/v1/vector/organizations/{self.organization_id}/users/invalid-uuid/integrations/{self.integration_id}/vectors/profiles'
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_get_profiles_invalid_uuid_in_path_integration(self):
        response = self.client.get(
            f'/v1/vector/organizations/{self.organization_id}/users/{self.user_id}/integrations/invalid-uuid/vectors/profiles'
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_different_integration_ids(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        integration_id_2 = uuid4()

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_profiles = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(
            return_value=[self.mock_vector_profiles[0]]
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(
            self._get_endpoint_url(integration_id=integration_id_2)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_vector_repo.get_profiles.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            integration_id=integration_id_2
        )

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_preserves_order(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_profiles = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(
            return_value=self.mock_vector_profiles
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data[0]['table_name'], 'users')
        self.assertEqual(data[1]['table_name'], 'orders')
        self.assertEqual(data[2]['table_name'], 'products')

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_response_content_type(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_profiles = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(
            return_value=self.mock_vector_profiles
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/json', response.headers['content-type'])

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_table_meta_conversion(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_profiles = AsyncMock()

        profile_with_dict_meta = MockVectorProfile(
            integration_id=self.integration_id,
            schema_name='public',
            table_name='test_table',
            table_meta={'key': 'value'}
        )

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(
            return_value=[profile_with_dict_meta]
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIsInstance(data[0]['table_meta'], str)

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    def test_get_profiles_cache_get_error(
            self,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(
            side_effect=Exception('Redis connection error')
        )

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('vector_service.api.router.profiles_router.get_current_identity')
    @patch('vector_service.api.router.profiles_router.VectorRepository')
    def test_get_profiles_cache_set_error(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_profiles = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_profiles = AsyncMock(
            side_effect=Exception('Redis write error')
        )

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_profiles = AsyncMock(
            return_value=self.mock_vector_profiles
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.get(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
