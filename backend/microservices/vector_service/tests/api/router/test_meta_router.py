import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from svc_vector_contracts.models import VectorMetaResponse, VectorMetaRequest
from vector_service.api.router.meta_router import router
from vector_service.database.exceptions import VectorGetFailed


class MockUserIdentity:
    def __init__(self, organization_id, user_id):
        self.organization_id = organization_id
        self.user_id = user_id


class MockVectorMeta:
    def __init__(self, integration_id, schema_name, table_name, table_meta):
        self.integration_id = integration_id
        self.schema_name = schema_name
        self.table_name = table_name
        self.table_meta = table_meta


class TestGetMetaEndpoint(unittest.TestCase):
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

        self.vector_ids = [uuid4(), uuid4(), uuid4()]
        self.request = VectorMetaRequest(vector_ids=self.vector_ids)

        self.user_identity = MockUserIdentity(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.table_meta_1 = {
            'integration_id': str(uuid4()),
            'schema_name': 'test',
            'table_name': 'test',
            'column_names': ['id', 'name', 'email']
        }
        self.table_meta_2 = {
            'integration_id': str(uuid4()),
            'schema_name': 'test1',
            'table_name': 'test1',
            'column_names': ['id1', 'name1', 'email1']
        }
        self.table_meta_3 = {
            'integration_id': str(uuid4()),
            'schema_name': 'test2',
            'table_name': 'test2',
            'column_names': ['id2', 'name2', 'email2']
        }

        self.mock_vector_metas = [
            MockVectorMeta(
                integration_id=self.integration_id,
                schema_name='public',
                table_name='users',
                table_meta=json.dumps(self.table_meta_1)
            ),
            MockVectorMeta(
                integration_id=self.integration_id,
                schema_name='public',
                table_name='orders',
                table_meta=json.dumps(self.table_meta_2)
            ),
            MockVectorMeta(
                integration_id=self.integration_id,
                schema_name='analytics',
                table_name='products',
                table_meta=json.dumps(self.table_meta_3)
            )
        ]

    def _get_endpoint_url(self, org_id=None, user_id=None):
        org_id = org_id or self.organization_id
        user_id = user_id or self.user_id
        return f'/v1/vector/organizations/{org_id}/users/{user_id}/integrations/vectors/meta'

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.VectorRepository')
    def test_get_meta_success_no_cache(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_metas = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vectors = AsyncMock(return_value=self.mock_vector_metas)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.post(
            self._get_endpoint_url(),
            json=self.request.model_dump(mode='json')
        )

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

        mock_vector_repo.get_vectors.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            vector_ids=self.vector_ids
        )

        self.mock_cache_service.set_vector_metas.assert_called_once()

    @patch('vector_service.api.router.meta_router.get_current_identity')
    def test_get_meta_success_from_cache(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        cached_response = [
            VectorMetaResponse(
                integration_id=self.integration_id,
                schema_name='public',
                table_name='users',
                table_meta=self.table_meta_1
            ),
            VectorMetaResponse(
                integration_id=self.integration_id,
                schema_name='public',
                table_name='orders',
                table_meta=self.table_meta_2
            )
        ]

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=cached_response)
        self.mock_cache_service.set_vector_metas = AsyncMock()

        response = self.client.post(
            self._get_endpoint_url(),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['table_name'], 'users')
        self.assertEqual(data[1]['table_name'], 'orders')

        self.mock_cache_service.get_vector_metas.assert_called_once()
        self.mock_cache_service.set_vector_metas.assert_not_called()

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.VectorRepository')
    def test_get_meta_with_empty_results(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_metas = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vectors = AsyncMock(return_value=[])
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.post(
            self._get_endpoint_url(),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

        self.mock_cache_service.set_vector_metas.assert_called_once()

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.logger')
    def test_get_meta_forbidden_wrong_organization(
            self,
            mock_logger,
            mock_get_identity
    ):
        wrong_org_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.post(
            self._get_endpoint_url(org_id=wrong_org_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': {'message': 'Forbidden'}})

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Forbidden request', log_call[0][0])
        self.assertEqual(log_call[1]['extra']['org_id'], wrong_org_id)

    @patch('vector_service.api.router.meta_router.get_current_identity')
    def test_get_meta_forbidden_wrong_user(self, mock_get_identity):
        wrong_user_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.post(
            self._get_endpoint_url(user_id=wrong_user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': {'message': 'Forbidden'}})

    @patch('vector_service.api.router.meta_router.get_current_identity')
    def test_get_meta_forbidden_both_wrong(self, mock_get_identity):
        wrong_org_id = uuid4()
        wrong_user_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.post(
            self._get_endpoint_url(org_id=wrong_org_id, user_id=wrong_user_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.VectorRepository')
    @patch('vector_service.api.router.meta_router.logger')
    def test_get_meta_database_error(
            self,
            mock_logger,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=None)

        error_msg = 'Database connection timeout'
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vectors = AsyncMock(
            side_effect=VectorGetFailed(error_msg)
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.post(
            self._get_endpoint_url(),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

        response_data = response.json()
        self.assertIn('Database error', response_data['detail']['message'])
        self.assertIn(error_msg, response_data['detail']['message'])

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Get vector metas failed with DB error', log_call[0][0])
        self.assertTrue(log_call[1]['exc_info'])

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.VectorRepository')
    @patch('vector_service.api.router.meta_router.logger')
    def test_get_meta_unexpected_error(
        self,
        mock_logger,
        mock_vector_repo_class,
        mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=None)

        error_msg = 'Unexpected network error'
        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vectors = AsyncMock(
            side_effect=RuntimeError(error_msg)
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.post(
            self._get_endpoint_url(),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = response.json()
        self.assertIn('Unexpected error', response_data['detail']['message'])
        self.assertIn(error_msg, response_data['detail']['message'])

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn('Unexpected get vector metas error', log_call[0][0])
        self.assertTrue(log_call[1]['exc_info'])

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.VectorRepository')
    def test_get_meta_json_decode_error(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=None)

        invalid_vector_meta = MockVectorMeta(
            integration_id=self.integration_id,
            schema_name='public',
            table_name='invalid',
            table_meta='not valid json{]['
        )

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vectors = AsyncMock(return_value=[invalid_vector_meta])
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.post(
            self._get_endpoint_url(),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.VectorRepository')
    def test_get_meta_with_single_vector(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_metas = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vectors = AsyncMock(
            return_value=[self.mock_vector_metas[0]]
        )
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.post(
            self._get_endpoint_url(),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['table_name'], 'users')

    def test_get_meta_missing_vector_ids_param(self):
        response = self.client.post(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.VectorRepository')
    def test_get_meta_with_empty_vector_ids(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_metas = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vectors = AsyncMock(return_value=[])
        mock_vector_repo_class.return_value = mock_vector_repo

        # Empty params list means no vector_ids sent, should fail validation
        response = self.client.post(
            self._get_endpoint_url(),
            params=[]
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_get_meta_invalid_uuid_in_path(self):
        response = self.client.post(
            f'/v1/vector/organizations/invalid-uuid/users/{self.user_id}/integrations/vectors/meta',
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.VectorRepository')
    def test_get_meta_preserves_vector_order(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_metas = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vectors = AsyncMock(return_value=self.mock_vector_metas)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.post(
            self._get_endpoint_url(),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data[0]['table_name'], 'users')
        self.assertEqual(data[1]['table_name'], 'orders')
        self.assertEqual(data[2]['table_name'], 'products')

    @patch('vector_service.api.router.meta_router.get_current_identity')
    @patch('vector_service.api.router.meta_router.VectorRepository')
    def test_get_meta_response_content_type(
            self,
            mock_vector_repo_class,
            mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_vector_metas = AsyncMock(return_value=None)
        self.mock_cache_service.set_vector_metas = AsyncMock()

        mock_vector_repo = MagicMock()
        mock_vector_repo.get_vectors = AsyncMock(return_value=self.mock_vector_metas)
        mock_vector_repo_class.return_value = mock_vector_repo

        response = self.client.post(
            self._get_endpoint_url(),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/json', response.headers['content-type'])
