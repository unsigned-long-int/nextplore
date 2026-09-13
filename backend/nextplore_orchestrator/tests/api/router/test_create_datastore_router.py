import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.connector import get_backend_connector
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.api.router.create_datastore_router import router
from nextplore_orchestrator.clients.integration import DataStoreCreateRemoteError
from nextplore_orchestrator.database.exceptions import KekIdGetFailed, KekIdNotFound
from svc_integration_contracts.models import DataStoreCreateRequest, Auth, Cloud, DB

ROUTER = "nextplore_orchestrator.api.router.create_datastore_router"
ENDPOINT = "/v1/nextplore-orchestrator/datastores"

VALID_PAYLOAD = {
    "auth": Auth.password_native,
    "cloud": Cloud.azure,
    "db": DB.postgresql,
    "connection_name": "prod-db",
    "descr": "Production database",
    "host": "db.internal",
    "database_name": "prod",
    "port": 5432,
    "username": "svc_user",
    "password": "s3cret",
}
INVALID_PAYLOAD = {**VALID_PAYLOAD, "port": "not-a-number"}
KEK_KID = "kek-kid-1"


class TestCreateDataStore(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app, raise_server_exceptions=False)

        self.user_identity = UserIdentity(organization_id=uuid4(), user_id=uuid4())

        self.session_mock = AsyncMock()
        self.backend_connector_mock = MagicMock()
        self.backend_connector_mock.session_scope.return_value.__aenter__.return_value = self.session_mock

        self.integration_client_mock = AsyncMock()
        self.integration_client_mock.create_datastore.return_value = None

        auth_repo_patcher = patch(f"{ROUTER}.AuthRepository")
        self.auth_repo_cls_mock = auth_repo_patcher.start()
        self.addCleanup(auth_repo_patcher.stop)
        self.auth_repo_mock = AsyncMock()
        self.auth_repo_mock.get_kek_kid.return_value = KEK_KID
        self.auth_repo_cls_mock.return_value = self.auth_repo_mock

        self.app.dependency_overrides = {
            get_active_user: lambda: self.user_identity,
            get_backend_connector: lambda: self.backend_connector_mock,
            get_integration_client: lambda: self.integration_client_mock,
        }

    def post(self, body=None):
        return self.client.post(ENDPOINT, json=VALID_PAYLOAD if body is None else body)

    def forwarded_kwargs(self):
        _, kwargs = self.integration_client_mock.create_datastore.call_args
        return kwargs


class TestSuccessfulCreation(TestCreateDataStore):
    def test_returns_201_on_success(self):
        response = self.post()

        self.assertEqual(response.status_code, 201)

    def test_returns_an_empty_body(self):
        response = self.post()

        self.assertEqual(response.content, b"")

    def test_forwards_the_request_enriched_with_the_kek_kid(self):
        self.post()

        payload = self.forwarded_kwargs()["payload"]
        self.assertIsInstance(payload, DataStoreCreateRequest)
        self.assertEqual(payload.kek_kid, KEK_KID)

    def test_does_not_mutate_the_original_request_fields(self):
        self.post()

        payload = self.forwarded_kwargs()["payload"]
        self.assertEqual(
            payload.model_dump(exclude={"kek_kid"}),
            DataStoreCreateRequest(**VALID_PAYLOAD).model_dump(exclude={"kek_kid"}),
        )

    def test_calls_the_client_exactly_once(self):
        self.post()

        self.integration_client_mock.create_datastore.assert_awaited_once()

    def test_overrides_a_client_supplied_kek_kid(self):
        self.post(body={**VALID_PAYLOAD, "kek_kid": "attacker-supplied"})

        self.assertEqual(self.forwarded_kwargs()["payload"].kek_kid, KEK_KID)

    def test_keeps_secret_fields_as_secrets(self):
        self.post()

        payload = self.forwarded_kwargs()["payload"]
        self.assertEqual(payload.password.get_secret_value(), "s3cret")
        self.assertNotIn("s3cret", repr(payload))


class TestKekLookup(TestCreateDataStore):
    def test_builds_the_auth_repository_on_the_scoped_session(self):
        self.post()

        self.auth_repo_cls_mock.assert_called_once_with(self.session_mock)

    def test_looks_up_the_kek_kid_for_the_organization(self):
        self.post()

        self.auth_repo_mock.get_kek_kid.assert_awaited_once_with(
            self.user_identity.organization_id
        )

    def test_kek_id_not_found_becomes_424(self):
        self.auth_repo_mock.get_kek_kid.side_effect = KekIdNotFound("no kek for org")

        response = self.post()

        self.assertEqual(response.status_code, 424)
        self.assertIn("no kek for org", response.json()["detail"]["message"])

    def test_kek_id_get_failed_becomes_424(self):
        self.auth_repo_mock.get_kek_kid.side_effect = KekIdGetFailed("db timeout")

        response = self.post()

        self.assertEqual(response.status_code, 424)
        self.assertIn("db timeout", response.json()["detail"]["message"])

    def test_does_not_call_the_client_when_kek_lookup_fails(self):
        self.auth_repo_mock.get_kek_kid.side_effect = KekIdNotFound("no kek for org")

        self.post()

        self.integration_client_mock.create_datastore.assert_not_awaited()

    def test_kek_failure_logs_the_traceback(self):
        self.auth_repo_mock.get_kek_kid.side_effect = KekIdNotFound("no kek for org")

        with self.assertLogs(level="ERROR") as captured:
            self.post()

        record = next(r for r in captured.records if "Kek" in r.message)
        self.assertIsNotNone(record.exc_info)
        self.assertEqual(record.org_id, self.user_identity.organization_id)


class TestRequestValidation(TestCreateDataStore):
    def test_missing_body_is_rejected_with_422(self):
        response = self.client.post(ENDPOINT)

        self.assertEqual(response.status_code, 422)

    def test_invalid_body_is_rejected_with_422(self):
        response = self.post(body=INVALID_PAYLOAD)

        self.assertEqual(response.status_code, 422)

    def test_does_not_touch_the_database_or_client_when_the_body_is_invalid(self):
        self.post(body=INVALID_PAYLOAD)

        self.backend_connector_mock.session_scope.assert_not_called()
        self.integration_client_mock.create_datastore.assert_not_awaited()


class TestIdentityPropagation(TestCreateDataStore):
    def test_forwards_the_organization_id(self):
        self.post()

        self.assertEqual(
            self.forwarded_kwargs()["organization_id"],
            self.user_identity.organization_id,
        )

    def test_forwards_the_user_id(self):
        self.post()

        self.assertEqual(self.forwarded_kwargs()["user_id"], self.user_identity.user_id)

    def test_passes_none_when_the_identity_lacks_the_attributes(self):
        class BareIdentity:
            pass

        self.app.dependency_overrides[get_active_user] = lambda: BareIdentity()

        self.post()

        self.auth_repo_mock.get_kek_kid.assert_awaited_once_with(None)
        kwargs = self.forwarded_kwargs()
        self.assertIsNone(kwargs["organization_id"])
        self.assertIsNone(kwargs["user_id"])


class TestRemoteErrorHandling(TestCreateDataStore):
    def setUp(self):
        super().setUp()
        self.integration_client_mock.create_datastore.side_effect = (
            DataStoreCreateRemoteError("integration service unreachable")
        )

    def test_remote_error_becomes_424(self):
        response = self.post()

        self.assertEqual(response.status_code, 424)

    def test_remote_error_detail_includes_the_message(self):
        response = self.post()

        self.assertIn(
            "integration service unreachable", response.json()["detail"]["message"]
        )

    def test_remote_error_logs_identity_context_and_traceback(self):
        with self.assertLogs(level="ERROR") as captured:
            self.post()

        record = next(r for r in captured.records if "remote" in r.message)
        self.assertIsNotNone(record.exc_info)
        self.assertEqual(record.org_id, self.user_identity.organization_id)
        self.assertEqual(record.user_id, self.user_identity.user_id)


class TestUnexpectedErrorHandling(TestCreateDataStore):
    def setUp(self):
        super().setUp()
        self.integration_client_mock.create_datastore.side_effect = RuntimeError(
            "postgres://user:pw@internal-host:5432 connection reset"
        )

    def test_unexpected_exception_becomes_500(self):
        response = self.post()

        self.assertEqual(response.status_code, 500)

    def test_500_detail_starts_with_the_generic_prefix(self):
        response = self.post()

        self.assertTrue(
            response.json()["detail"]["message"].startswith("Unexpected error")
        )

    def test_500_leaks_internal_details(self):
        response = self.post()

        self.assertIn("internal-host", response.text)

    def test_unexpected_error_logs_the_identity_context(self):
        with self.assertLogs(level="ERROR") as captured:
            self.post()

        record = next(r for r in captured.records if "unexpected" in r.message)
        self.assertEqual(record.org_id, self.user_identity.organization_id)
        self.assertEqual(record.user_id, self.user_identity.user_id)

    def test_unexpected_error_in_kek_lookup_also_becomes_500(self):
        self.integration_client_mock.create_datastore.side_effect = None
        self.auth_repo_mock.get_kek_kid.side_effect = RuntimeError("kaboom")

        response = self.post()

        self.assertEqual(response.status_code, 500)
        self.integration_client_mock.create_datastore.assert_not_awaited()


class TestAuthentication(TestCreateDataStore):
    def _reject(self):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_request_is_rejected(self):
        self.app.dependency_overrides[get_active_user] = self._reject

        response = self.post()

        self.assertEqual(response.status_code, 401)

    def test_does_not_touch_the_database_or_client_when_unauthenticated(self):
        self.app.dependency_overrides[get_active_user] = self._reject

        self.post()

        self.backend_connector_mock.session_scope.assert_not_called()
        self.integration_client_mock.create_datastore.assert_not_awaited()
