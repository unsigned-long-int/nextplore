import datetime
import unittest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_integration_contracts.models import CertProfile, CertState

from integration_service.cache import get_cache_service
from integration_service.domain.models.cert import CertProfile as CertProfileDomain
from integration_service.api.router.cert_profiles_router import router
from integration_service.api.dependencies import get_backend_connector
from integration_service.database.exceptions import CertGetFailed


class TestCertProfilesRouter(unittest.TestCase):
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
        self.domain_profile = CertProfileDomain(
            id=uuid4(),
            state=CertState.pending,
            public_cert_pem='--PEM---',
            thumbprint_sha256='THUMB...',
            cert_name='my-cert',
            not_before=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc),
            cert_kid='kid',
            created_at=datetime.datetime.now(datetime.timezone.utc),
            assigned_at=None,
            revoked_at=None

        )

    def _url(self, org_id, user_id) -> str:
        return (
            f'/v1/integration/organizations/{org_id}/'
            f'users/{user_id}/integrations/certificates/profiles'
        )

    @patch('integration_service.api.router.cert_profiles_router.get_current_identity')
    def test_returns_cached_cert_profiles(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        cached = [
            CertProfile(
                id=uuid4(),
                state=CertState.active,
                cert_kid='test-kid',
                public_cert_pem='---PEM',
                cert_name='my-cert',
                thumbprint_sha256='SHA256...',
                not_before=datetime.datetime.now(datetime.timezone.utc),
                not_after=datetime.datetime.now(datetime.timezone.utc),
                created_at=datetime.datetime.now(datetime.timezone.utc),
                assigned_at=None,
                activated_at=None,
                revoked_at=None,
            )
        ]
        self.cache_mock.get_cert_profiles.return_value = cached

        response = self.client.get(self._url(user_identity_mock.organization_id, user_identity_mock.user_id))

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), [item.model_dump(mode='json') for item in cached])
        self.cache_mock.get_cert_profiles.assert_awaited_once_with(user_identity=user_identity_mock)
        self.cache_mock.set_cert_profiles.assert_not_awaited()

    @patch('integration_service.api.router.cert_profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.cert_profiles_router.get_current_identity')
    def test_requests_cert_profiles_and_sets_cache(
        self,
        get_current_identity_mock,
        integration_repo_cls_mock,
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock
        self.cache_mock.get_cert_profiles.return_value = None

        integration_repo_instance = AsyncMock()
        integration_repo_instance.get_cert_profiles.return_value = [self.domain_profile]
        integration_repo_cls_mock.return_value = integration_repo_instance

        expected_dto = CertProfile(
            id=self.domain_profile.id,
            state=CertState.pending,
            cert_kid=self.domain_profile.cert_kid,
            public_cert_pem=self.domain_profile.public_cert_pem,
            thumbprint_sha256=self.domain_profile.thumbprint_sha256,
            cert_name=self.domain_profile.cert_name,
            not_before=self.domain_profile.not_before,
            not_after=self.domain_profile.not_after,
            created_at=self.domain_profile.created_at,
            assigned_at=self.domain_profile.assigned_at,
            activated_at=getattr(self.domain_profile, 'activated_at', None),
            revoked_at=self.domain_profile.revoked_at,
        )

        response = self.client.get(self._url(user_identity_mock.organization_id, user_identity_mock.user_id))

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), [expected_dto.model_dump(mode='json')])

        integration_repo_cls_mock.assert_called_once_with(self.database_backend_connector_mock)
        integration_repo_instance.get_cert_profiles.assert_awaited_once_with(
            organization_id=user_identity_mock.organization_id,
            user_id=user_identity_mock.user_id,
        )

        self.cache_mock.set_cert_profiles.assert_awaited_once()
        kwargs = self.cache_mock.set_cert_profiles.await_args.kwargs
        self.assertEqual(kwargs['user_identity'], user_identity_mock)
        self.assertEqual(kwargs['response'], [expected_dto])

    @patch('integration_service.api.router.cert_profiles_router.get_current_identity')
    def test_forbidden_when_identity_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        response = self.client.get(self._url(uuid4(), uuid4()))
        self.assertEqual(403, response.status_code)
        self.assertEqual(response.json(), {'detail': {'message': 'Forbidden'}})

        self.cache_mock.get_cert_profiles.assert_not_called()

    @patch('integration_service.api.router.cert_profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.cert_profiles_router.get_current_identity')
    def test_db_error_returns_424(self, get_current_identity_mock, integration_repo_cls_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_cert_profiles.return_value = None
        integration_repo_instance = AsyncMock()
        integration_repo_instance.get_cert_profiles.side_effect = CertGetFailed('boom')
        integration_repo_cls_mock.return_value = integration_repo_instance

        response = self.client.get(self._url(user_identity_mock.organization_id, user_identity_mock.user_id))

        self.assertEqual(424, response.status_code)
        self.assertIn('Database error: boom', response.text)

    @patch('integration_service.api.router.cert_profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.cert_profiles_router.get_current_identity')
    def test_unexpected_error_returns_500(self, get_current_identity_mock, integration_repo_cls_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_cert_profiles.return_value = None
        integration_repo_instance = AsyncMock()
        integration_repo_instance.get_cert_profiles.side_effect = RuntimeError('explode')
        integration_repo_cls_mock.return_value = integration_repo_instance

        response = self.client.get(self._url(user_identity_mock.organization_id, user_identity_mock.user_id))

        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected error: explode', response.text)
