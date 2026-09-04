import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.api.router.cert_profiles_router import router
from nextplore_orchestrator.clients.integration import CertGetProfilesRemoteError
from nextplore_orchestrator.clients.integration.models.cert_profile import CertProfile
from nextplore_orchestrator.clients.integration.models.cert_state import CertState

ENDPOINT = "/v1/nextplore-orchestrator/datastores/certificates/profiles"


def make_profile(**overrides) -> CertProfile:
    payload = {
        "id": uuid4(),
        "cert_name": "prod-db-cert",
        "state": CertState.ACTIVE,
        "cert_kid": "kid-1",
        "public_cert_pem": "pub",
        "thumbprint_sha256": "sha256",
        "not_before": datetime.now(timezone.utc),
        "not_after": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }
    payload.update(overrides)
    return CertProfile(**payload)


class TestCertProfiles(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app, raise_server_exceptions=False)

        self.user_identity = UserIdentity(organization_id=uuid4(), user_id=uuid4())

        self.integration_client_mock = AsyncMock()
        self.integration_client_mock.get_cert_profiles.return_value = []

        self.app.dependency_overrides = {
            get_active_user: lambda: self.user_identity,
            get_integration_client: lambda: self.integration_client_mock,
        }

    def get(self):
        return self.client.get(ENDPOINT)


class TestSuccessfulRetrieval(TestCertProfiles):
    def test_returns_200_on_success(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

    def test_returns_the_profiles_from_the_client(self):
        first_id, second_id = uuid4(), uuid4()
        self.integration_client_mock.get_cert_profiles.return_value = [
            make_profile(id=first_id),
            make_profile(id=second_id, cert_name="staging-cert"),
        ]

        response = self.get()

        self.assertEqual(
            [item["id"] for item in response.json()],
            [str(first_id), str(second_id)],
        )

    def test_returns_an_empty_list_when_there_are_no_profiles(self):
        self.integration_client_mock.get_cert_profiles.return_value = []

        response = self.get()

        self.assertEqual(response.json(), [])

    def test_strips_fields_not_in_the_response_model(self):
        self.integration_client_mock.get_cert_profiles.return_value = [make_profile()]

        response = self.get()

        self.assertTrue(set(response.json()[0]).issubset(set(CertProfile.model_fields)))


class TestIdentityPropagation(TestCertProfiles):
    def test_forwards_the_organization_id(self):
        self.get()

        _, kwargs = self.integration_client_mock.get_cert_profiles.call_args
        self.assertEqual(kwargs["organization_id"], self.user_identity.organization_id)

    def test_forwards_the_user_id(self):
        self.get()

        _, kwargs = self.integration_client_mock.get_cert_profiles.call_args
        self.assertEqual(kwargs["user_id"], self.user_identity.user_id)

    def test_calls_the_client_exactly_once(self):
        self.get()

        self.integration_client_mock.get_cert_profiles.assert_awaited_once()

    def test_passes_none_when_the_identity_lacks_the_attributes(self):
        class BareIdentity:
            pass

        self.app.dependency_overrides[get_active_user] = lambda: BareIdentity()

        self.get()

        self.integration_client_mock.get_cert_profiles.assert_awaited_once_with(
            organization_id=None, user_id=None
        )


class TestRemoteErrorHandling(TestCertProfiles):
    def test_cert_get_profiles_remote_error_becomes_424(self):
        self.integration_client_mock.get_cert_profiles.side_effect = (
            CertGetProfilesRemoteError("integration service unreachable")
        )

        response = self.get()

        self.assertEqual(response.status_code, 424)

    def test_remote_error_detail_includes_the_message(self):
        self.integration_client_mock.get_cert_profiles.side_effect = (
            CertGetProfilesRemoteError("integration service unreachable")
        )

        response = self.get()

        self.assertIn(
            "integration service unreachable", response.json()["detail"]["message"]
        )

    def test_remote_error_logs_the_identity_context(self):
        self.integration_client_mock.get_cert_profiles.side_effect = (
            CertGetProfilesRemoteError("down")
        )

        with self.assertLogs(level="ERROR") as captured:
            self.get()

        record = next(r for r in captured.records if "remote" in r.message)
        self.assertEqual(record.org_id, self.user_identity.organization_id)

    def test_remote_error_logs_the_traceback(self):
        self.integration_client_mock.get_cert_profiles.side_effect = (
            CertGetProfilesRemoteError("down")
        )

        with self.assertLogs(level="ERROR") as captured:
            self.get()

        record = next(r for r in captured.records if "remote" in r.message)
        self.assertIsNotNone(record.exc_info)


class TestUnexpectedErrorHandling(TestCertProfiles):
    def test_unexpected_exception_becomes_500(self):
        self.integration_client_mock.get_cert_profiles.side_effect = RuntimeError(
            "kaboom"
        )

        response = self.get()

        self.assertEqual(response.status_code, 500)

    def test_500_detail_is_generic(self):
        self.integration_client_mock.get_cert_profiles.side_effect = RuntimeError(
            "kaboom"
        )

        response = self.get()

        self.assertEqual(
            response.json()["detail"]["message"], "Unexpected server error"
        )

    def test_500_does_not_leak_internal_details(self):
        self.integration_client_mock.get_cert_profiles.side_effect = RuntimeError(
            "postgres://user:pw@internal-host:5432 connection reset"
        )

        response = self.get()

        self.assertNotIn("internal-host", response.text)

    def test_unexpected_error_logs_the_traceback(self):
        self.integration_client_mock.get_cert_profiles.side_effect = RuntimeError(
            "kaboom"
        )

        with self.assertLogs(level="ERROR") as captured:
            self.get()

        record = next(r for r in captured.records if "unexpected" in r.message)
        self.assertIsNotNone(record.exc_info)

    def test_unexpected_error_logs_the_original_message(self):
        self.integration_client_mock.get_cert_profiles.side_effect = RuntimeError(
            "kaboom"
        )

        with self.assertLogs(level="ERROR") as captured:
            self.get()

        self.assertIn("kaboom", captured.output[0])


class TestAuthentication(TestCertProfiles):
    def _reject(self):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_request_is_rejected(self):
        self.app.dependency_overrides[get_active_user] = self._reject

        response = self.get()

        self.assertEqual(response.status_code, 401)

    def test_does_not_call_the_client_when_unauthenticated(self):
        self.app.dependency_overrides[get_active_user] = self._reject

        self.get()

        self.integration_client_mock.get_cert_profiles.assert_not_awaited()
