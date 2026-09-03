import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from integration_service.api.dependencies import get_llm_service
from integration_service.api.router.user_llm_profiles_router import router
from integration_service.database.exceptions import UserLlmGetFailed


class MockUserIdentity:
    def __init__(self, organization_id, user_id):
        self.organization_id = organization_id
        self.user_id = user_id


class MockUserLlmProfile:
    def __init__(
        self, provider, model_id, label, tags, api_base, max_tokens, model_ref_id
    ):
        self.provider = provider
        self.model_id = model_id
        self.label = label
        self.tags = tags
        self.api_base = api_base
        self.max_tokens = max_tokens
        self.model_ref_id = model_ref_id


class TestGetUserLlmProfilesRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)

        self.llm_service_mock = AsyncMock()

        self.app.dependency_overrides = {
            get_llm_service: lambda: self.llm_service_mock,
        }

        self.client = TestClient(self.app)

        self.organization_id = uuid4()
        self.user_id = uuid4()

        self.user_identity = MockUserIdentity(
            organization_id=self.organization_id,
            user_id=self.user_id,
        )

        self.mock_llm_profiles = [
            MockUserLlmProfile(
                provider="openai",
                model_id="gpt-4o",
                label="GPT-4o",
                tags=["chat", "vision"],
                max_tokens=2300,
                model_ref_id=uuid4(),
                api_base="https-test-api",
            ),
            MockUserLlmProfile(
                provider="anthropic",
                model_id="claude-sonnet-4-6",
                label="Claude Sonnet",
                tags=["chat"],
                max_tokens=2300,
                model_ref_id=uuid4(),
                api_base="https-test-api",
            ),
        ]

    def _url(self, org_id=None, user_id=None) -> str:
        org_id = org_id or self.organization_id
        user_id = user_id or self.user_id
        return f"/v1/integration/organizations/{org_id}/users/{user_id}/llm/profiles"

    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_returns_llm_profiles_successfully(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.user_identity
        self.llm_service_mock.get_user_llm_profiles.return_value = (
            self.mock_llm_profiles
        )

        response = self.client.get(self._url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_returns_empty_list_when_no_profiles(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.user_identity
        self.llm_service_mock.get_user_llm_profiles.return_value = []

        response = self.client.get(self._url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_calls_service_with_user_identity(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.user_identity
        self.llm_service_mock.get_user_llm_profiles.return_value = []

        self.client.get(self._url())

        self.llm_service_mock.get_user_llm_profiles.assert_awaited_once_with(
            self.user_identity
        )

    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_returns_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.user_identity

        response = self.client.get(self._url(user_id=uuid4()))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["detail"]["message"], "Forbidden")
        self.llm_service_mock.get_user_llm_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_returns_forbidden_when_org_id_mismatch(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.user_identity

        response = self.client.get(self._url(org_id=uuid4()))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["detail"]["message"], "Forbidden")
        self.llm_service_mock.get_user_llm_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_returns_forbidden_when_both_ids_mismatch(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.user_identity

        response = self.client.get(self._url(org_id=uuid4(), user_id=uuid4()))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.llm_service_mock.get_user_llm_profiles.assert_not_awaited()

    @patch("integration_service.api.router.user_llm_profiles_router.logger")
    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_logs_forbidden_with_org_and_user_id(
        self, get_current_identity_mock, mock_logger
    ):
        get_current_identity_mock.return_value = self.user_identity
        wrong_org_id = uuid4()

        self.client.get(self._url(org_id=wrong_org_id))

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn("Forbidden request", log_call[0][0])
        self.assertEqual(log_call[1]["extra"]["org_id"], wrong_org_id)

    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_returns_424_when_db_error(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.user_identity
        self.llm_service_mock.get_user_llm_profiles.side_effect = UserLlmGetFailed(
            "DB timeout"
        )

        response = self.client.get(self._url())

        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertIn("Database error", response.json()["detail"]["message"])
        self.assertIn("DB timeout", response.json()["detail"]["message"])

    @patch("integration_service.api.router.user_llm_profiles_router.logger")
    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_logs_db_error_with_exc_info(self, get_current_identity_mock, mock_logger):
        get_current_identity_mock.return_value = self.user_identity
        self.llm_service_mock.get_user_llm_profiles.side_effect = UserLlmGetFailed(
            "DB timeout"
        )

        self.client.get(self._url())

        mock_logger.error.assert_called_once()
        self.assertTrue(mock_logger.error.call_args[1]["exc_info"])

    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_returns_500_when_unexpected_error(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.user_identity
        self.llm_service_mock.get_user_llm_profiles.side_effect = RuntimeError("boom")

        response = self.client.get(self._url())

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Unexpected error", response.json()["detail"]["message"])
        self.assertIn("boom", response.json()["detail"]["message"])

    @patch("integration_service.api.router.user_llm_profiles_router.logger")
    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_logs_unexpected_error_with_exc_info(
        self, get_current_identity_mock, mock_logger
    ):
        get_current_identity_mock.return_value = self.user_identity
        self.llm_service_mock.get_user_llm_profiles.side_effect = RuntimeError("boom")

        self.client.get(self._url())

        mock_logger.error.assert_called_once()
        self.assertTrue(mock_logger.error.call_args[1]["exc_info"])

    def test_returns_422_for_invalid_org_uuid(self):
        response = self.client.get(
            f"/v1/integration/organizations/not-a-uuid/users/{self.user_id}/llm/profiles"
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_returns_422_for_invalid_user_uuid(self):
        response = self.client.get(
            f"/v1/integration/organizations/{self.organization_id}/users/not-a-uuid/llm/profiles"
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch(
        "integration_service.api.router.user_llm_profiles_router.get_current_identity"
    )
    def test_response_content_type_is_json(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.user_identity
        self.llm_service_mock.get_user_llm_profiles.return_value = []

        response = self.client.get(self._url())

        self.assertIn("application/json", response.headers["content-type"])
