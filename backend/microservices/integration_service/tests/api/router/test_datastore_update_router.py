import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_integration_contracts.models import DataStoreUpdateRequest

from integration_service.api.dependencies.get_service import get_data_store_service
from integration_service.api.router.datastore_update_router import router
from integration_service.database.exceptions import (
    DataStoreUpdateFailed,
    KekKidGetFailed,
)


class TestUpdateRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.datastore_service_mock = AsyncMock()

        self.app.dependency_overrides = {
            get_data_store_service: lambda: self.datastore_service_mock,
        }

        self.request = DataStoreUpdateRequest(
            connection_name="updated-connection",
            host="updated-host.com",
            port=5433,
            database_name="updated_db",
            autosync_on=True,
        )

    def _url(self, org_id, user_id, datastore_id) -> str:
        return (
            f"/v1/integration/organizations/{org_id}/"
            f"users/{user_id}/datastores/{datastore_id}"
        )

    @patch(
        "integration_service.api.router.datastore_update_router.get_current_identity"
    )
    def test_updates_datastore_successfully(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id,
            ),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(204, response.status_code)

        self.datastore_service_mock.update_datastore.assert_awaited_once_with(
            user_identity=user_identity_mock,
            datastore_id=datastore_id,
            payload=self.request,
        )

    @patch(
        "integration_service.api.router.datastore_update_router.get_current_identity"
    )
    def test_returns_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_user_id = uuid4()
        datastore_id = uuid4()

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id, different_user_id, datastore_id
            ),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.json()["detail"]["message"])

        self.datastore_service_mock.update_datastore.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_update_router.get_current_identity"
    )
    def test_returns_forbidden_when_org_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_org_id = uuid4()
        datastore_id = uuid4()

        response = self.client.patch(
            self._url(different_org_id, user_identity_mock.user_id, datastore_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.json()["detail"]["message"])

        self.datastore_service_mock.update_datastore.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_update_router.get_current_identity"
    )
    def test_raises_exception_when_datastore_update_failed(
        self, get_current_identity_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        self.datastore_service_mock.update_datastore.side_effect = (
            DataStoreUpdateFailed("Data store not found")
        )

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id,
            ),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            "Database error: Data store not found", response.json()["detail"]["message"]
        )

    @patch(
        "integration_service.api.router.datastore_update_router.get_current_identity"
    )
    def test_raises_exception_when_kek_kid_get_failed(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        self.datastore_service_mock.update_datastore.side_effect = KekKidGetFailed(
            "Failed to retrieve KEK KID"
        )

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id,
            ),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            "Database error: Failed to retrieve KEK KID",
            response.json()["detail"]["message"],
        )

    @patch(
        "integration_service.api.router.datastore_update_router.get_current_identity"
    )
    def test_raises_exception_when_generic_error(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        self.datastore_service_mock.update_datastore.side_effect = RuntimeError(
            "Unexpected error"
        )

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id,
            ),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(500, response.status_code)
        self.assertIn(
            "Unexpected error while updating data_store: Unexpected error",
            response.json()["detail"]["message"],
        )

    @patch(
        "integration_service.api.router.datastore_update_router.get_current_identity"
    )
    def test_passes_correct_parameters_to_service(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id,
            ),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(204, response.status_code)

        self.datastore_service_mock.update_datastore.assert_awaited_once()
        call_kwargs = self.datastore_service_mock.update_datastore.call_args[1]

        self.assertEqual(call_kwargs["user_identity"], user_identity_mock)
        self.assertEqual(call_kwargs["datastore_id"], datastore_id)
        self.assertEqual(
            call_kwargs["payload"].connection_name, self.request.connection_name
        )
        self.assertEqual(call_kwargs["payload"].host, self.request.host)
        self.assertEqual(call_kwargs["payload"].port, self.request.port)
        self.assertEqual(
            call_kwargs["payload"].database_name, self.request.database_name
        )
        self.assertEqual(call_kwargs["payload"].autosync_on, self.request.autosync_on)

    @patch(
        "integration_service.api.router.datastore_update_router.get_current_identity"
    )
    def test_validates_both_user_id_and_org_id_match(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        datastore_id = uuid4()

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                datastore_id,
            ),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(204, response.status_code)
        self.datastore_service_mock.update_datastore.assert_awaited_once()

    @patch(
        "integration_service.api.router.datastore_update_router.get_current_identity"
    )
    def test_prevents_update_with_mismatched_credentials(
        self, get_current_identity_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_org_id = uuid4()
        different_user_id = uuid4()
        datastore_id = uuid4()

        response = self.client.patch(
            self._url(different_org_id, different_user_id, datastore_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(403, response.status_code)
        self.datastore_service_mock.update_datastore.assert_not_awaited()
