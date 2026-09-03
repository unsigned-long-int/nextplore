import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from nextplore_sdk.encryptor.exc.exceptions import AzureCertCreationFailed
from svc_integration_contracts.models import CertCreateRequest

from integration_service.api.dependencies import get_backend_connector
from integration_service.api.router.create_certificate_router import router
from integration_service.cache import get_cache_service
from integration_service.database.exceptions import CertCreateFailed


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

    def _url(self, org_id, user_id) -> str:
        return (
            f"/v1/integration/organizations/{org_id}/"
            f"users/{user_id}/datastores/certificates"
        )

    @patch(
        "integration_service.api.router.create_certificate_router.DataStoreRepository"
    )
    @patch("integration_service.api.router.create_certificate_router.CertGenerator")
    @patch(
        "integration_service.api.router.create_certificate_router.get_current_identity"
    )
    def test_creates_certificate_successfully(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        cert_mock = MagicMock()
        cert_generator_instance = MagicMock()
        cert_generator_instance.create_cert.return_value = cert_mock
        cert_generator_mock.return_value = cert_generator_instance

        repo_instance = AsyncMock()
        integration_repo_mock.return_value = repo_instance

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(204, response.status_code)

        cert_generator_instance.create_cert.assert_called_once_with(
            key_size=self.request.key_size,
            validity_in_months=self.request.validity_in_months,
        )

        repo_instance.create_cert.assert_awaited_once_with(
            organization_id=user_identity_mock.organization_id,
            user_id=user_identity_mock.user_id,
            cert=cert_mock,
        )

        self.cache_mock.delete_datastore_cert_profiles.assert_awaited_once_with(
            user_identity_mock
        )

    @patch(
        "integration_service.api.router.create_certificate_router.get_current_identity"
    )
    def test_returns_forbidden_when_org_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_org_id = uuid4()

        response = self.client.post(
            self._url(different_org_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.json()["detail"]["message"])

    @patch(
        "integration_service.api.router.create_certificate_router.get_current_identity"
    )
    def test_returns_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_user_id = uuid4()

        response = self.client.post(
            self._url(user_identity_mock.organization_id, different_user_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.json()["detail"]["message"])

    @patch(
        "integration_service.api.router.create_certificate_router.DataStoreRepository"
    )
    @patch("integration_service.api.router.create_certificate_router.CertGenerator")
    @patch(
        "integration_service.api.router.create_certificate_router.get_current_identity"
    )
    def test_raises_exception_when_azure_cert_creation_failed(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        cert_generator_instance = MagicMock()
        cert_generator_instance.create_cert.side_effect = AzureCertCreationFailed(
            "Azure vault error"
        )
        cert_generator_mock.return_value = cert_generator_instance

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            "AKV Error: Azure vault error", response.json()["detail"]["message"]
        )
        self.cache_mock.delete_datastore_cert_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.create_certificate_router.DataStoreRepository"
    )
    @patch("integration_service.api.router.create_certificate_router.CertGenerator")
    @patch(
        "integration_service.api.router.create_certificate_router.get_current_identity"
    )
    def test_handles_cert_create_failed_exception(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        cert_mock = MagicMock()
        cert_generator_instance = MagicMock()
        cert_generator_instance.create_cert.return_value = cert_mock
        cert_generator_mock.return_value = cert_generator_instance

        repo_instance = AsyncMock()
        repo_instance.create_cert.side_effect = CertCreateFailed("Database error")
        integration_repo_mock.return_value = repo_instance

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(204, response.status_code)
        self.cache_mock.delete_datastore_cert_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.create_certificate_router.DataStoreRepository"
    )
    @patch("integration_service.api.router.create_certificate_router.CertGenerator")
    @patch(
        "integration_service.api.router.create_certificate_router.get_current_identity"
    )
    def test_raises_exception_when_generic_error(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        cert_generator_instance = MagicMock()
        cert_generator_instance.create_cert.side_effect = RuntimeError(
            "Unexpected error"
        )
        cert_generator_mock.return_value = cert_generator_instance

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(500, response.status_code)
        self.assertIn(
            "Unexpected error: Unexpected error", response.json()["detail"]["message"]
        )
        self.cache_mock.delete_datastore_cert_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.create_certificate_router.DataStoreRepository"
    )
    @patch("integration_service.api.router.create_certificate_router.CertGenerator")
    @patch(
        "integration_service.api.router.create_certificate_router.get_current_identity"
    )
    def test_uses_default_purpose_when_not_provided(
        self, get_current_identity_mock, cert_generator_mock, integration_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        request_without_purpose = CertCreateRequest(
            key_size=2048, validity_in_months=12
        )

        cert_mock = MagicMock()
        cert_generator_instance = MagicMock()
        cert_generator_instance.create_cert.return_value = cert_mock
        cert_generator_mock.return_value = cert_generator_instance

        repo_instance = AsyncMock()
        integration_repo_mock.return_value = repo_instance

        response = self.client.post(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id),
            json=request_without_purpose.model_dump(mode="json"),
        )

        self.assertEqual(204, response.status_code)

        expected_cert_name = f"cert-{user_identity_mock.organization_id!s}-{user_identity_mock.user_id!s}-general"
        cert_generator_mock.assert_called_once_with(expected_cert_name)
