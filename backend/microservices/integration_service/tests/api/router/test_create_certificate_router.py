import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from azure.core.exceptions import AzureError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from nextplore_sdk.encryptor.exc.exceptions import AzureCertCreationFailed
from svc_integration_contracts.models import CertCreateRequest

from integration_service.api.dependencies import get_backend_connector
from integration_service.api.router.create_certificate_router import router
from integration_service.cache import get_cache_service
from integration_service.database.exceptions import CertCreateFailed

ROUTER = "integration_service.api.router.create_certificate_router"


class TestCreateCertificateRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.cache_mock = AsyncMock()
        self.database_backend_connector_mock = AsyncMock()

        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_backend_connector: lambda: self.database_backend_connector_mock,
        }

        self.request = CertCreateRequest(
            key_size=2048, validity_in_months=12, purpose="general"
        )

    @staticmethod
    def _identity(get_current_identity_mock):
        identity = MagicMock()
        identity.user_id = uuid4()
        identity.organization_id = uuid4()
        get_current_identity_mock.return_value = identity
        return identity

    @staticmethod
    def _generator(cert_generator_mock, *, returns=None, raises=None):
        instance = MagicMock()
        if raises is not None:
            instance.create_cert.side_effect = raises
        else:
            instance.create_cert.return_value = returns
        cert_generator_mock.return_value = instance
        return instance

    @staticmethod
    def _repo(integration_repo_mock, *, raises=None):
        instance = AsyncMock()
        if raises is not None:
            instance.create_cert.side_effect = raises
        integration_repo_mock.return_value = instance
        return instance

    def _url(self, org_id, user_id) -> str:
        return (
            f"/v1/integration/organizations/{org_id}/"
            f"users/{user_id}/datastores/certificates"
        )

    def _post(self, identity, request=None):
        request = request or self.request
        return self.client.post(
            self._url(identity.organization_id, identity.user_id),
            json=request.model_dump(mode="json"),
        )

    @patch(f"{ROUTER}.DataStoreRepository")
    @patch(f"{ROUTER}.CertGenerator")
    @patch(f"{ROUTER}.get_current_identity")
    def test_creates_certificate_successfully(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        identity = self._identity(get_current_identity_mock)
        cert_mock = MagicMock()
        generator = self._generator(cert_generator_mock, returns=cert_mock)
        repo = self._repo(integration_repo_mock)

        response = self._post(identity)

        self.assertEqual(204, response.status_code)
        generator.create_cert.assert_called_once_with(
            key_size=self.request.key_size,
            validity_in_months=self.request.validity_in_months,
        )
        repo.create_cert.assert_awaited_once_with(
            organization_id=identity.organization_id,
            user_id=identity.user_id,
            cert=cert_mock,
        )
        self.cache_mock.delete_datastore_cert_profiles.assert_awaited_once_with(
            identity
        )

    @patch(f"{ROUTER}.DataStoreRepository")
    @patch(f"{ROUTER}.CertGenerator")
    @patch(f"{ROUTER}.get_current_identity")
    def test_uses_default_purpose_when_not_provided(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        identity = self._identity(get_current_identity_mock)
        self._generator(cert_generator_mock, returns=MagicMock())
        self._repo(integration_repo_mock)
        request_without_purpose = CertCreateRequest(
            key_size=2048, validity_in_months=12
        )

        response = self._post(identity, request_without_purpose)

        self.assertEqual(204, response.status_code)
        cert_generator_mock.assert_called_once_with(
            f"cert-{identity.organization_id!s}-{identity.user_id!s}-general"
        )

    @patch(f"{ROUTER}.get_current_identity")
    def test_returns_forbidden_when_org_id_mismatch(self, get_current_identity_mock):
        identity = self._identity(get_current_identity_mock)

        response = self.client.post(
            self._url(uuid4(), identity.user_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.json()["detail"]["message"])

    @patch(f"{ROUTER}.get_current_identity")
    def test_returns_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        identity = self._identity(get_current_identity_mock)

        response = self.client.post(
            self._url(identity.organization_id, uuid4()),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.json()["detail"]["message"])

    @patch(f"{ROUTER}.DataStoreRepository")
    @patch(f"{ROUTER}.CertGenerator")
    @patch(f"{ROUTER}.get_current_identity")
    def test_azure_cert_creation_failure_becomes_424(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        identity = self._identity(get_current_identity_mock)
        self._generator(
            cert_generator_mock, raises=AzureCertCreationFailed("Azure vault error")
        )
        repo = self._repo(integration_repo_mock)

        response = self._post(identity)

        self.assertEqual(424, response.status_code)
        self.assertIn(
            "AKV Error: Azure vault error", response.json()["detail"]["message"]
        )
        repo.create_cert.assert_not_awaited()
        self.cache_mock.delete_datastore_cert_profiles.assert_not_awaited()

    @patch(f"{ROUTER}.DataStoreRepository")
    @patch(f"{ROUTER}.CertGenerator")
    @patch(f"{ROUTER}.get_current_identity")
    def test_unexpected_generation_error_becomes_generic_500(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        identity = self._identity(get_current_identity_mock)
        self._generator(cert_generator_mock, raises=RuntimeError("secret internals"))
        repo = self._repo(integration_repo_mock)

        response = self._post(identity)

        self.assertEqual(500, response.status_code)
        self.assertEqual(
            "Unexpected server error", response.json()["detail"]["message"]
        )
        self.assertNotIn("secret internals", response.text)
        repo.create_cert.assert_not_awaited()
        self.cache_mock.delete_datastore_cert_profiles.assert_not_awaited()

    @patch(f"{ROUTER}.DataStoreRepository")
    @patch(f"{ROUTER}.CertGenerator")
    @patch(f"{ROUTER}.get_current_identity")
    def test_db_failure_rolls_back_akv_cert_and_returns_500(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        identity = self._identity(get_current_identity_mock)
        generator = self._generator(cert_generator_mock, returns=MagicMock())
        self._repo(integration_repo_mock, raises=CertCreateFailed("Database error"))

        response = self._post(identity)

        self.assertEqual(500, response.status_code)
        self.assertEqual(
            "Failed to persist certificate record",
            response.json()["detail"]["message"],
        )
        generator.cert_client.begin_delete_certificate.assert_called_once_with(
            f"cert-{identity.organization_id!s}-{identity.user_id!s}-general"
        )
        self.cache_mock.delete_datastore_cert_profiles.assert_not_awaited()

    @patch(f"{ROUTER}.DataStoreRepository")
    @patch(f"{ROUTER}.CertGenerator")
    @patch(f"{ROUTER}.get_current_identity")
    def test_db_failure_still_returns_500_when_rollback_fails(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        identity = self._identity(get_current_identity_mock)
        generator = self._generator(cert_generator_mock, returns=MagicMock())
        generator.cert_client.begin_delete_certificate.side_effect = AzureError(
            "vault unreachable"
        )
        self._repo(integration_repo_mock, raises=CertCreateFailed("Database error"))

        with self.assertLogs(level="ERROR") as captured:
            response = self._post(identity)

        self.assertEqual(500, response.status_code)
        self.assertEqual(
            "Failed to persist certificate record",
            response.json()["detail"]["message"],
        )
        self.assertTrue(
            any("roll back" in r.message for r in captured.records),
            "rollback failure should be logged",
        )
        self.cache_mock.delete_datastore_cert_profiles.assert_not_awaited()

    @patch(f"{ROUTER}.DataStoreRepository")
    @patch(f"{ROUTER}.CertGenerator")
    @patch(f"{ROUTER}.get_current_identity")
    def test_unexpected_persistence_error_becomes_generic_500(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        identity = self._identity(get_current_identity_mock)
        generator = self._generator(cert_generator_mock, returns=MagicMock())
        self._repo(integration_repo_mock, raises=RuntimeError("secret internals"))

        response = self._post(identity)

        self.assertEqual(500, response.status_code)
        self.assertEqual(
            "Unexpected server error", response.json()["detail"]["message"]
        )
        self.assertNotIn("secret internals", response.text)
        generator.cert_client.begin_delete_certificate.assert_not_called()
        self.cache_mock.delete_datastore_cert_profiles.assert_not_awaited()
