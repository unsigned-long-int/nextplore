import unittest
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from svc_integration_contracts.models import (
    DataStoreCreateRequest,
    Auth,
    DB,
    Cloud
)

from nextplore_sdk.database.connection_maker.models.auth import Auth as DomainAuth
from nextplore_sdk.database.connection_maker.models.db import DB as DomainDB
from nextplore_sdk.database.connection_maker.models.cloud import Cloud as DomainCloud
from integration_service.api.router.datastore_test_router import router
from integration_service.api.dependencies import get_engine_manager

class TestTestRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.engine_manager_mock = AsyncMock()

        self.app.dependency_overrides = {
            get_engine_manager: lambda: self.engine_manager_mock,
        }

        self.postgres_request = DataStoreCreateRequest(
            connection_name='test-postgres',
            descr='test-descr',
            cloud=Cloud.aws,
            auth=Auth.iam,
            db=DB.postgresql,
            host='localhost',
            port=5432,
            database_name='testdb',
            username=SecretStr('testuser'),
            password=SecretStr('testpass'),
            kek_kid='test-kek-kid'
        )

        self.snowflake_request = DataStoreCreateRequest(
            connection_name='test-snowflake',
            descr='test-descr',
            cloud=Cloud.snowflake_managed,
            auth=Auth.cert,
            db=DB.snowflake,
            host='account.snowflakecomputing.com',
            port=443,
            database_name='analytics',
            warehouse='compute_wh',
            username=SecretStr('snowflake_user'),
            azure_cert_kid='cert-kid-123',
            azure_cert_name='cert-name-123',
            tenant_id='tenant-123',
            client_id='client-123',
            kek_kid='test-kek-kid'
        )


        self.aws_request = DataStoreCreateRequest(
            connection_name='test-aws',
            descr='test-descr',
            cloud=Cloud.aws,
            auth=Auth.iam,
            db=DB.mysql,
            host='aws-db.rds.amazonaws.com',
            port=5432,
            database_name='awsdb',
            aws_external_id=SecretStr('external-id-123'),
            aws_role_arn=SecretStr('arn:aws:iam::123456789012:role/MyRole'),
            region='us-east-1',
            kek_kid='test-kek-kid'
        )

    def _url(self) -> str:
        return '/v1/integration/datastores/test'

    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_tests_postgres_datastore_successfully(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock
    ):
        to_domain_cloud_mock.return_value = DomainCloud.AWS
        to_domain_auth_mock.return_value = DomainAuth.IAM
        to_domain_db_mock.return_value = DomainDB.POSTGRESQL

        profile_instance = MagicMock()
        connection_profile_mock.return_value = profile_instance

        connection_mock = MagicMock()
        connection_mock.__enter__ = MagicMock(return_value=connection_mock)
        connection_mock.__exit__ = MagicMock(return_value=False)
        connection_mock.execute = MagicMock()

        engine_mock = MagicMock()
        engine_mock.connect.return_value = connection_mock
        self.engine_manager_mock.acquire_engine.return_value = engine_mock

        payload = self.postgres_request.model_dump()
        payload["aws_external_id"] = self.postgres_request.aws_external_id.get_secret_value() if self.postgres_request.aws_external_id else None
        payload["aws_role_arn"] = self.postgres_request.aws_role_arn.get_secret_value() if self.postgres_request.aws_role_arn else None
        payload["password"] = self.postgres_request.password.get_secret_value() if self.postgres_request.password else None
        payload["client_secret"] = self.postgres_request.client_secret.get_secret_value() if self.postgres_request.client_secret else None
        payload['username'] = self.postgres_request.username.get_secret_value() if self.postgres_request.username else None

        response = self.client.post(self._url(), json=payload)

        self.assertEqual(204, response.status_code)

        to_domain_cloud_mock.assert_called_once_with('aws')
        to_domain_auth_mock.assert_called_once_with('iam')
        to_domain_db_mock.assert_called_once_with('postgresql')

        connection_profile_mock.assert_called_once()
        call_kwargs = connection_profile_mock.call_args[1]
        self.assertEqual(call_kwargs['host'], 'localhost')
        self.assertEqual(call_kwargs['port'], 5432)
        self.assertEqual(call_kwargs['database'], 'testdb')
        self.assertEqual(call_kwargs['username'], 'testuser')
        self.assertEqual(call_kwargs['password'], 'testpass')

        self.engine_manager_mock.acquire_engine.assert_awaited_once_with(profile_instance)

        connection_mock.execute.assert_called_once()

    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_tests_snowflake_datastore_with_certificate(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock
    ):
        to_domain_cloud_mock.return_value = DomainCloud.SNOWFLAKE_MANAGED
        to_domain_auth_mock.return_value = DomainAuth.CERT
        to_domain_db_mock.return_value = DomainDB.SNOWFLAKE

        profile_instance = MagicMock()
        connection_profile_mock.return_value = profile_instance

        connection_mock = MagicMock()
        connection_mock.__enter__ = MagicMock(return_value=connection_mock)
        connection_mock.__exit__ = MagicMock(return_value=False)
        connection_mock.execute = MagicMock()

        engine_mock = MagicMock()
        engine_mock.connect.return_value = connection_mock
        self.engine_manager_mock.acquire_engine.return_value = engine_mock

        response = self.client.post(
            self._url(),
            json=self.snowflake_request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        connection_profile_mock.assert_called_once()
        call_kwargs = connection_profile_mock.call_args[1]
        self.assertEqual(call_kwargs['warehouse'], 'compute_wh')
        self.assertEqual(call_kwargs['azure_cert_kid'], 'cert-kid-123')
        self.assertEqual(call_kwargs['azure_cert_name'], 'cert-name-123')
        self.assertEqual(call_kwargs['tenant_id'], 'tenant-123')
        self.assertEqual(call_kwargs['client_id'], 'client-123')

    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_tests_aws_datastore_with_role(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock
    ):
        to_domain_cloud_mock.return_value = DomainCloud.AWS
        to_domain_auth_mock.return_value = DomainAuth.IAM
        to_domain_db_mock.return_value = DomainDB.MYSQL

        profile_instance = MagicMock()
        connection_profile_mock.return_value = profile_instance

        connection_mock = MagicMock()
        connection_mock.__enter__ = MagicMock(return_value=connection_mock)
        connection_mock.__exit__ = MagicMock(return_value=False)
        connection_mock.execute = MagicMock()

        engine_mock = MagicMock()
        engine_mock.connect.return_value = connection_mock
        self.engine_manager_mock.acquire_engine.return_value = engine_mock

        payload = self.aws_request.model_dump()
        payload['aws_external_id'] = self.aws_request.aws_external_id.get_secret_value()
        payload['aws_role_arn'] = self.aws_request.aws_role_arn.get_secret_value()
        payload['password'] = self.aws_request.password.get_secret_value() if self.aws_request.password else None
        payload['client_secret'] = self.aws_request.client_secret.get_secret_value() if self.aws_request.client_secret else None

        response = self.client.post(self._url(), json=payload)

        self.assertEqual(204, response.status_code)

        connection_profile_mock.assert_called_once()
        call_kwargs = connection_profile_mock.call_args[1]
        self.assertEqual(call_kwargs['aws_external_id'], 'external-id-123')
        self.assertEqual(call_kwargs['aws_role_arn'], 'arn:aws:iam::123456789012:role/MyRole')
        self.assertEqual(call_kwargs['region'], 'us-east-1')

    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_raises_exception_when_connection_fails(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock
    ):
        to_domain_cloud_mock.return_value = DomainCloud.AWS
        to_domain_auth_mock.return_value = DomainAuth.IAM
        to_domain_db_mock.return_value = DomainDB.POSTGRESQL

        profile_instance = MagicMock()
        connection_profile_mock.return_value = profile_instance

        self.engine_manager_mock.acquire_engine.side_effect = OperationalError(
            'Connection refused',
            params=None,
            orig=None
        )

        response = self.client.post(
            self._url(),
            json=self.postgres_request.model_dump(mode='json')
        )

        self.assertEqual(424, response.status_code)
        self.assertIn('Database error:', response.json()['detail']['message'])

    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_raises_exception_when_query_execution_fails(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock
    ):
        to_domain_cloud_mock.return_value = DomainCloud.AWS
        to_domain_auth_mock.return_value = DomainAuth.IAM
        to_domain_db_mock.return_value = DomainDB.POSTGRESQL

        profile_instance = MagicMock()
        connection_profile_mock.return_value = profile_instance

        connection_mock = MagicMock()
        connection_mock.__enter__ = MagicMock(return_value=connection_mock)
        connection_mock.__exit__ = MagicMock(return_value=False)
        connection_mock.execute.side_effect = SQLAlchemyError('Query execution failed')

        engine_mock = MagicMock()
        engine_mock.connect.return_value = connection_mock
        self.engine_manager_mock.acquire_engine.return_value = engine_mock

        response = self.client.post(
            self._url(),
            json=self.postgres_request.model_dump(mode='json')
        )

        self.assertEqual(424, response.status_code)
        self.assertIn('Database error: Query execution failed', response.json()['detail']['message'])

    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_raises_exception_when_generic_error(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock
    ):
        to_domain_cloud_mock.return_value = DomainCloud.AWS
        to_domain_auth_mock.return_value = DomainAuth.IAM
        to_domain_db_mock.return_value = DomainDB.POSTGRESQL

        connection_profile_mock.side_effect = RuntimeError('Unexpected error')

        response = self.client.post(
            self._url(),
            json=self.postgres_request.model_dump(mode='json')
        )

        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected error: Unexpected error', response.json()['detail']['message'])

    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_extracts_secret_values_from_secret_str_fields(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock
    ):
        to_domain_cloud_mock.return_value = DomainCloud.AWS
        to_domain_auth_mock.return_value = DomainAuth.IAM
        to_domain_db_mock.return_value = DomainDB.POSTGRESQL

        profile_instance = MagicMock()
        connection_profile_mock.return_value = profile_instance

        connection_mock = MagicMock()
        connection_mock.__enter__ = MagicMock(return_value=connection_mock)
        connection_mock.__exit__ = MagicMock(return_value=False)
        connection_mock.execute = MagicMock()

        engine_mock = MagicMock()
        engine_mock.connect.return_value = connection_mock
        self.engine_manager_mock.acquire_engine.return_value = engine_mock

        payload = self.postgres_request.model_dump()
        payload["aws_external_id"] = self.postgres_request.aws_external_id.get_secret_value() if self.postgres_request.aws_external_id else None
        payload["aws_role_arn"] = self.postgres_request.aws_role_arn.get_secret_value() if self.postgres_request.aws_role_arn else None
        payload["password"] = self.postgres_request.password.get_secret_value() if self.postgres_request.password else None
        payload["client_secret"] = self.postgres_request.client_secret.get_secret_value() if self.postgres_request.client_secret else None
        payload['username'] = self.postgres_request.username.get_secret_value() if self.postgres_request.username else None

        response = self.client.post(self._url(), json=payload)

        self.assertEqual(204, response.status_code)

        connection_profile_mock.assert_called_once()
        call_kwargs = connection_profile_mock.call_args[1]
        self.assertEqual(call_kwargs['username'], 'testuser')
        self.assertEqual(call_kwargs['password'], 'testpass')
        self.assertIsInstance(call_kwargs['username'], str)
        self.assertIsInstance(call_kwargs['password'], str)

    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_handles_optional_fields_as_none(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock
    ):
        to_domain_cloud_mock.return_value = DomainCloud.GCP
        to_domain_auth_mock.return_value = DomainAuth.PASSWORD_PROXY
        to_domain_db_mock.return_value = DomainDB.SQLSERVER

        minimal_request = DataStoreCreateRequest(
            connection_name='test-minimal',
            descr='test-descr',
            cloud=Cloud.gcp,
            auth=Auth.password_proxy,
            db=DB.sqlserver,
            host='localhost',
            port=5432,
            database_name='testdb',
            kek_kid='test-kek-kid'
        )

        profile_instance = MagicMock()
        connection_profile_mock.return_value = profile_instance

        connection_mock = MagicMock()
        connection_mock.__enter__ = MagicMock(return_value=connection_mock)
        connection_mock.__exit__ = MagicMock(return_value=False)
        connection_mock.execute = MagicMock()

        engine_mock = MagicMock()
        engine_mock.connect.return_value = connection_mock
        self.engine_manager_mock.acquire_engine.return_value = engine_mock

        response = self.client.post(
            self._url(),
            json=minimal_request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        connection_profile_mock.assert_called_once()
        call_kwargs = connection_profile_mock.call_args[1]
        self.assertIsNone(call_kwargs['username'])
        self.assertIsNone(call_kwargs['password'])
        self.assertIsNone(call_kwargs['warehouse'])
        self.assertIsNone(call_kwargs['client_secret'])
        self.assertIsNone(call_kwargs['aws_external_id'])
        self.assertIsNone(call_kwargs['aws_role_arn'])
        self.assertIsNone(call_kwargs['snowflake_private_key'])

    @patch('integration_service.api.router.datastore_test_router.text')
    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_executes_select_1_test_query(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock,
        text_mock
    ):
        to_domain_cloud_mock.return_value = 'none'
        to_domain_auth_mock.return_value = 'postgres'
        to_domain_db_mock.return_value = 'postgres'

        profile_instance = MagicMock()
        connection_profile_mock.return_value = profile_instance

        text_mock.return_value = 'SELECT 1'

        connection_mock = MagicMock()
        connection_mock.__enter__ = MagicMock(return_value=connection_mock)
        connection_mock.__exit__ = MagicMock(return_value=False)
        connection_mock.execute = MagicMock()

        engine_mock = MagicMock()
        engine_mock.connect.return_value = connection_mock
        self.engine_manager_mock.acquire_engine.return_value = engine_mock

        response = self.client.post(
            self._url(),
            json=self.postgres_request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        text_mock.assert_called_once_with('SELECT 1')
        connection_mock.execute.assert_called_once_with('SELECT 1')

    @patch('integration_service.api.router.datastore_test_router.to_domain_db')
    @patch('integration_service.api.router.datastore_test_router.to_domain_auth')
    @patch('integration_service.api.router.datastore_test_router.to_domain_cloud')
    @patch('integration_service.api.router.datastore_test_router.ConnectionProfile')
    def test_uses_context_manager_for_connection(
        self,
        connection_profile_mock,
        to_domain_cloud_mock,
        to_domain_auth_mock,
        to_domain_db_mock
    ):
        to_domain_cloud_mock.return_value = 'none'
        to_domain_auth_mock.return_value = 'postgres'
        to_domain_db_mock.return_value = 'postgres'

        profile_instance = MagicMock()
        connection_profile_mock.return_value = profile_instance

        connection_mock = MagicMock()
        enter_mock = MagicMock(return_value=connection_mock)
        exit_mock = MagicMock(return_value=False)
        connection_mock.__enter__ = enter_mock
        connection_mock.__exit__ = exit_mock
        connection_mock.execute = MagicMock()

        engine_mock = MagicMock()
        engine_mock.connect.return_value = connection_mock
        self.engine_manager_mock.acquire_engine.return_value = engine_mock

        response = self.client.post(
            self._url(),
            json=self.postgres_request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        enter_mock.assert_called_once()
        exit_mock.assert_called_once()