import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from svc_integration_contracts.models import DB, Auth, Cloud, DataStoreCreateRequest

from integration_service.api.dependencies import get_data_store_service
from integration_service.api.router.datastore_create_router import router
from integration_service.database.exceptions import (
    DataStoreCreateFailed,
    SecretsCreateFailed,
)


class TestCreateDataStoreRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.mock_integration_service = AsyncMock()

        self.app.dependency_overrides = {
            get_data_store_service: lambda: self.mock_integration_service
        }

        self.organization_id = uuid4()
        self.user_id = uuid4()

        self.request_payload = DataStoreCreateRequest(
            auth=Auth.iam,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name="test-connection",
            descr="test-descr",
            host="localhost",
            database_name="test-database",
            port=5432,
            kek_kid="test-kek-kid",
        )

    def tearDown(self):
        self.app.dependency_overrides = {}

    def _url(self, org_id, user_id) -> str:
        return f"/v1/integration/organizations/{org_id}/users/{user_id}/datastores"

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_create_datastore_success(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 204)
        self.mock_integration_service.create_datastore.assert_awaited_once_with(
            user_identity=user_identity, payload=self.request_payload
        )

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_returns_forbidden_when_organization_id_mismatch(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = uuid4()
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["message"], "Forbidden")
        self.mock_integration_service.create_datastore.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_returns_forbidden_when_user_id_mismatch(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = uuid4()
        mock_get_identity.return_value = user_identity

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["message"], "Forbidden")
        self.mock_integration_service.create_datastore.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_returns_forbidden_when_both_ids_mismatch(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = uuid4()
        user_identity.user_id = uuid4()
        mock_get_identity.return_value = user_identity

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["message"], "Forbidden")
        self.mock_integration_service.create_datastore.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_returns_424_when_integration_create_failed(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        error_message = "Database connection error"
        self.mock_integration_service.create_datastore.side_effect = (
            DataStoreCreateFailed(error_message)
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 424)
        self.assertIn("Database error:", response.json()["detail"]["message"])
        self.assertIn(error_message, response.json()["detail"]["message"])

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_returns_424_when_secrets_create_failed(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        error_message = "Secret encryption failed"
        self.mock_integration_service.create_datastore.side_effect = (
            SecretsCreateFailed(error_message)
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 424)
        self.assertIn("Database error:", response.json()["detail"]["message"])
        self.assertIn(error_message, response.json()["detail"]["message"])

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_returns_500_when_unexpected_error(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        error_message = "Unexpected runtime error"
        self.mock_integration_service.create_datastore.side_effect = RuntimeError(
            error_message
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Unexpected error while creating data store:",
            response.json()["detail"]["message"],
        )
        self.assertIn(error_message, response.json()["detail"]["message"])

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    @patch("integration_service.api.router.datastore_create_router.logger")
    def test_logs_forbidden_request(self, mock_logger, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = uuid4()
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 403)
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        self.assertIn("Forbidden request", log_message)

        extra_data = mock_logger.error.call_args[1]["extra"]
        self.assertEqual(extra_data["org_id"], self.organization_id)
        self.assertEqual(extra_data["user_id"], self.user_id)

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    @patch("integration_service.api.router.datastore_create_router.logger")
    def test_logs_integration_create_failed_error(self, mock_logger, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        error_message = "Database connection error"
        self.mock_integration_service.create_datastore.side_effect = (
            DataStoreCreateFailed(error_message)
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 424)
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        self.assertIn("Create data store failed with DB error", log_message)
        self.assertIn(error_message, log_message)
        self.assertEqual(mock_logger.error.call_args[1]["exc_info"], True)

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    @patch("integration_service.api.router.datastore_create_router.logger")
    def test_logs_unexpected_error(self, mock_logger, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        error_message = "Unexpected error"
        self.mock_integration_service.create_datastore.side_effect = ValueError(
            error_message
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 500)
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        self.assertIn("Unexpected create data store error", log_message)
        self.assertIn(error_message, log_message)
        self.assertEqual(mock_logger.error.call_args[1]["exc_info"], True)

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_service_called_with_correct_parameters(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 204)

        call_args = self.mock_integration_service.create_datastore.call_args
        self.assertEqual(call_args[1]["user_identity"], user_identity)

        payload_arg = call_args[1]["payload"]
        self.assertIsInstance(payload_arg, DataStoreCreateRequest)
        self.assertEqual(payload_arg.connection_name, "test-connection")
        self.assertEqual(payload_arg.host, "localhost")
        self.assertEqual(payload_arg.database_name, "test-database")

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_handles_different_auth_types(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        oauth2_payload = DataStoreCreateRequest(
            auth=Auth.iam,
            cloud=Cloud.azure,
            db=DB.postgresql,
            connection_name="oauth2-connection",
            descr="test-descr",
            host="localhost",
            database_name="testdb",
            port=5432,
            kek_kid="test-kek-kid",
            client_secret=SecretStr("secret123"),
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=oauth2_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 204)

        call_args = self.mock_integration_service.create_datastore.call_args
        payload_arg = call_args[1]["payload"]
        self.assertEqual(payload_arg.auth, Auth.iam)

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_handles_different_cloud_providers(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        azure_payload = DataStoreCreateRequest(
            auth=Auth.iam,
            cloud=Cloud.azure,
            db=DB.sqlserver,
            connection_name="azure-connection",
            descr="test-descr",
            host="localhost",
            database_name="testdb",
            port=1433,
            kek_kid="test-kek-kid",
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=azure_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 204)

        call_args = self.mock_integration_service.create_datastore.call_args
        payload_arg = call_args[1]["payload"]
        self.assertEqual(payload_arg.cloud, Cloud.azure)
        self.assertEqual(payload_arg.db, DB.sqlserver)

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_returns_empty_body_on_success(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_service_not_called_when_forbidden(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = uuid4()
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 403)
        self.mock_integration_service.create_datastore.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_handles_custom_kek_kid(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        custom_kek_kid = "https://vault.azure.net/keys/custom-key/version123"
        custom_payload = DataStoreCreateRequest(
            auth=Auth.iam,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name="test-connection",
            descr="test-descr",
            host="localhost",
            database_name="testdb",
            port=5432,
            kek_kid=custom_kek_kid,
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=custom_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 204)

        call_args = self.mock_integration_service.create_datastore.call_args
        payload_arg = call_args[1]["payload"]
        self.assertEqual(payload_arg.kek_kid, custom_kek_kid)

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_error_response_format_for_database_errors(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        error_message = "Connection timeout"
        self.mock_integration_service.create_datastore.side_effect = (
            DataStoreCreateFailed(error_message)
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 424)
        response_json = response.json()
        self.assertIn("detail", response_json)
        self.assertIn("message", response_json["detail"])
        self.assertEqual(
            response_json["detail"]["message"], f"Database error: {error_message}"
        )

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_error_response_format_for_unexpected_errors(self, mock_get_identity):
        user_identity = MagicMock()
        user_identity.organization_id = self.organization_id
        user_identity.user_id = self.user_id
        mock_get_identity.return_value = user_identity

        error_message = "Memory allocation failed"
        self.mock_integration_service.create_datastore.side_effect = MemoryError(
            error_message
        )

        response = self.client.post(
            self._url(self.organization_id, self.user_id),
            json=self.request_payload.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, 500)
        response_json = response.json()
        self.assertIn("detail", response_json)
        self.assertIn("message", response_json["detail"])
        self.assertEqual(
            response_json["detail"]["message"],
            f"Unexpected error while creating data store: {error_message}",
        )


class TestCreateDataStoreRouterEdgeCases(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.mock_integration_service = AsyncMock()
        self.app.dependency_overrides = {
            get_data_store_service: lambda: self.mock_integration_service
        }

    def tearDown(self):
        self.app.dependency_overrides = {}

    def _url(self, org_id, user_id) -> str:
        return f"/v1/integration/organizations/{org_id}/users/{user_id}/datastores"

    @patch(
        "integration_service.api.router.datastore_create_router.get_current_identity"
    )
    def test_handles_zero_uuid(self, mock_get_identity):
        zero_uuid = UUID("00000000-0000-0000-0000-000000000000")
        user_identity = MagicMock()
        user_identity.organization_id = zero_uuid
        user_identity.user_id = zero_uuid
        mock_get_identity.return_value = user_identity

        payload = DataStoreCreateRequest(
            auth=Auth.iam,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name="test",
            descr="test-descr",
            host="localhost",
            database_name="testdb",
            port=5432,
            kek_kid="test-kek",
        )

        response = self.client.post(
            self._url(zero_uuid, zero_uuid), json=payload.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, 204)

    def test_invalid_json_returns_422(self):
        response = self.client.post(
            self._url(uuid4(), uuid4()), json={"invalid": "data"}
        )

        self.assertEqual(response.status_code, 422)
