import unittest
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.api.router.create_cert_router import router
from nextplore_orchestrator.clients.integration import CertCreateRemoteError
from svc_integration_contracts.models import CertCreateRequest

ENDPOINT = "/v1/nextplore-orchestrator/datastores/certificates"

VALID_PAYLOAD = {
    "purpose": "prod-db",
    "key_size": 128,
    "validity_in_months": 12,
}


class TestCreateCertificate(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app, raise_server_exceptions=False)

        self.user_identity = UserIdentity(organization_id=uuid4(), user_id=uuid4())

        self.integration_client_mock = AsyncMock()
        self.integration_client_mock.create_cert.return_value = None

        self.app.dependency_overrides = {
            get_active_user: lambda: self.user_identity,
            get_integration_client: lambda: self.integration_client_mock,
        }

    def post(self, body=None):
        return self.client.post(ENDPOINT, json=VALID_PAYLOAD if body is None else body)


class TestSuccessfulCreation(TestCreateCertificate):
    def test_returns_201_on_success(self):
        response = self.post()

        self.assertEqual(response.status_code, 201)

    def test_returns_an_empty_body(self):
        response = self.post()

        self.assertEqual(response.content, b"")

    def test_forwards_the_parsed_request_as_payload(self):
        self.post()

        _, kwargs = self.integration_client_mock.create_cert.call_args
        self.assertIsInstance(kwargs["payload"], CertCreateRequest)
        self.assertEqual(kwargs["payload"], CertCreateRequest(**VALID_PAYLOAD))


INVALID_PAYLOAD = {**VALID_PAYLOAD, "key_size": "not-a-number"}


class TestRequestValidation(TestCreateCertificate):
    def test_missing_body_is_rejected_with_422(self):
        response = self.client.post(ENDPOINT)

        self.assertEqual(response.status_code, 422)

    def test_invalid_body_is_rejected_with_422(self):
        response = self.post(body=INVALID_PAYLOAD)

        self.assertEqual(response.status_code, 422)

    def test_does_not_call_the_client_when_the_body_is_invalid(self):
        self.post(body=INVALID_PAYLOAD)

        self.integration_client_mock.create_cert.assert_not_awaited()


class TestIdentityPropagation(TestCreateCertificate):
    def test_forwards_the_organization_id(self):
        self.post()

        _, kwargs = self.integration_client_mock.create_cert.call_args
        self.assertEqual(kwargs["organization_id"], self.user_identity.organization_id)

    def test_forwards_the_user_id(self):
        self.post()

        _, kwargs = self.integration_client_mock.create_cert.call_args
        self.assertEqual(kwargs["user_id"], self.user_identity.user_id)

    def test_calls_the_client_exactly_once(self):
        self.post()

        self.integration_client_mock.create_cert.assert_awaited_once()

    def test_passes_none_when_the_identity_lacks_the_attributes(self):
        class BareIdentity:
            pass

        self.app.dependency_overrides[get_active_user] = lambda: BareIdentity()

        self.post()

        _, kwargs = self.integration_client_mock.create_cert.call_args
        self.assertIsNone(kwargs["organization_id"])
        self.assertIsNone(kwargs["user_id"])


class TestRemoteErrorHandling(TestCreateCertificate):
    def test_cert_create_remote_error_becomes_424(self):
        self.integration_client_mock.create_cert.side_effect = CertCreateRemoteError(
            "integration service unreachable"
        )

        response = self.post()

        self.assertEqual(response.status_code, 424)

    def test_remote_error_detail_includes_the_message(self):
        self.integration_client_mock.create_cert.side_effect = CertCreateRemoteError(
            "integration service unreachable"
        )

        response = self.post()

        self.assertIn(
            "integration service unreachable", response.json()["detail"]["message"]
        )

    def test_remote_error_logs_the_identity_context(self):
        self.integration_client_mock.create_cert.side_effect = CertCreateRemoteError(
            "down"
        )

        with self.assertLogs(level="ERROR") as captured:
            self.post()

        record = next(r for r in captured.records if "remote" in r.message)
        self.assertEqual(record.org_id, self.user_identity.organization_id)
        self.assertEqual(record.user_id, self.user_identity.user_id)

    def test_remote_error_logs_the_traceback(self):
        self.integration_client_mock.create_cert.side_effect = CertCreateRemoteError(
            "down"
        )

        with self.assertLogs(level="ERROR") as captured:
            self.post()

        record = next(r for r in captured.records if "remote" in r.message)
        self.assertIsNotNone(record.exc_info)


class TestUnexpectedErrorHandling(TestCreateCertificate):
    def test_unexpected_exception_becomes_500(self):
        self.integration_client_mock.create_cert.side_effect = RuntimeError("kaboom")

        response = self.post()

        self.assertEqual(response.status_code, 500)

    def test_500_detail_is_generic(self):
        self.integration_client_mock.create_cert.side_effect = RuntimeError("kaboom")

        response = self.post()

        self.assertEqual(
            response.json()["detail"]["message"], "Unexpected server error"
        )

    def test_500_does_not_leak_internal_details(self):
        self.integration_client_mock.create_cert.side_effect = RuntimeError(
            "postgres://user:pw@internal-host:5432 connection reset"
        )

        response = self.post()

        self.assertNotIn("internal-host", response.text)

    def test_unexpected_error_logs_the_traceback(self):
        self.integration_client_mock.create_cert.side_effect = RuntimeError("kaboom")

        with self.assertLogs(level="ERROR") as captured:
            self.post()

        record = next(r for r in captured.records if "unexpected" in r.message)
        self.assertIsNotNone(record.exc_info)

    def test_unexpected_error_logs_the_original_message(self):
        self.integration_client_mock.create_cert.side_effect = RuntimeError("kaboom")

        with self.assertLogs(level="ERROR") as captured:
            self.post()

        self.assertIn("kaboom", captured.output[0])


class TestAuthentication(TestCreateCertificate):
    def _reject(self):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_request_is_rejected(self):
        self.app.dependency_overrides[get_active_user] = self._reject

        response = self.post()

        self.assertEqual(response.status_code, 401)

    def test_does_not_call_the_client_when_unauthenticated(self):
        self.app.dependency_overrides[get_active_user] = self._reject

        self.post()

        self.integration_client_mock.create_cert.assert_not_awaited()
