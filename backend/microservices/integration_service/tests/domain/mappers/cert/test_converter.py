import unittest
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock

from integration_service.domain.mappers.cert import (
    cert_create_from_dto,
    orm_from_cert,
    cert_profile_from_orm
)
from integration_service.api.models.cert_create_request import CertCreateRequest
from integration_service.domain.models.cert import CertCreate, CertProfile, CertState
from integration_service.database.models import CertORM
from nextplore_sdk.encryptor.models.cert import Cert


class TestCertMappers(unittest.TestCase):
    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.now = datetime.utcnow()

    def test_cert_create_from_dto_maps_all_fields(self):
        cert_create_request = CertCreateRequest(
            purpose='authentication',
            key_size=2048,
            validity_in_months=12
        )

        result = cert_create_from_dto(cert_create_request)

        self.assertIsInstance(result, CertCreate)
        self.assertEqual(result.purpose, 'authentication')
        self.assertEqual(result.key_size, 2048)
        self.assertEqual(result.validity_in_months, 12)

    def test_cert_create_from_dto_with_default_purpose(self):
        cert_create_request = CertCreateRequest(
            purpose=None,
            key_size=4096,
            validity_in_months=24
        )

        result = cert_create_from_dto(cert_create_request)

        self.assertIsNone(result.purpose)
        self.assertEqual(result.key_size, 4096)
        self.assertEqual(result.validity_in_months, 24)

    def test_cert_create_from_dto_with_different_key_sizes(self):
        for key_size in [2048, 3072, 4096]:
            cert_create_request = CertCreateRequest(
                purpose='test',
                key_size=key_size,
                validity_in_months=12
            )

            result = cert_create_from_dto(cert_create_request)

            self.assertEqual(result.key_size, key_size)

    def test_orm_from_cert_maps_all_fields(self):
        cert = Cert(
            cert_kid='cert-kid-123',
            cert_name='test-cert',
            public_cert_pem='-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----',
            thumbprint_sha256='abc123def456',
            not_before=self.now,
            not_after=self.now
        )

        result = orm_from_cert(
            organization_id=self.organization_id,
            user_id=self.user_id,
            cert=cert
        )

        self.assertIsInstance(result, CertORM)
        self.assertEqual(result.organization_id, self.organization_id)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.cert_kid, 'cert-kid-123')
        self.assertEqual(result.cert_name, 'test-cert')
        self.assertEqual(result.public_cert_pem, '-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----')
        self.assertEqual(result.thumbprint_sha256, 'abc123def456')
        self.assertEqual(result.not_before, self.now)
        self.assertEqual(result.not_after, self.now)

    def test_orm_from_cert_with_different_organizations(self):
        org_id_1 = uuid4()
        org_id_2 = uuid4()

        cert = Cert(
            cert_kid='cert-kid',
            cert_name='cert-name',
            public_cert_pem='cert-pem',
            thumbprint_sha256='thumbprint',
            not_before=self.now,
            not_after=self.now
        )

        result_1 = orm_from_cert(organization_id=org_id_1, user_id=self.user_id, cert=cert)
        result_2 = orm_from_cert(organization_id=org_id_2, user_id=self.user_id, cert=cert)

        self.assertEqual(result_1.organization_id, org_id_1)
        self.assertEqual(result_2.organization_id, org_id_2)
        self.assertNotEqual(result_1.organization_id, result_2.organization_id)

    def test_cert_profile_from_orm_maps_all_fields(self):
        cert_orm = MagicMock(spec=CertORM)
        cert_orm.id = uuid4()
        cert_orm.state = CertState.ACTIVE
        cert_orm.public_cert_pem = '-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----'
        cert_orm.thumbprint_sha256 = 'abc123def456'
        cert_orm.not_before = self.now
        cert_orm.not_after = self.now
        cert_orm.cert_kid = 'cert-kid-123'
        cert_orm.cert_name = 'test-cert'
        cert_orm.created_at = self.now
        cert_orm.assigned_at = self.now
        cert_orm.revoked_at = None

        result = cert_profile_from_orm(cert_orm)

        self.assertIsInstance(result, CertProfile)
        self.assertEqual(result.id, cert_orm.id)
        self.assertEqual(result.state, CertState.ACTIVE)
        self.assertEqual(result.public_cert_pem, cert_orm.public_cert_pem)
        self.assertEqual(result.thumbprint_sha256, cert_orm.thumbprint_sha256)
        self.assertEqual(result.not_before, self.now)
        self.assertEqual(result.not_after, self.now)
        self.assertEqual(result.cert_kid, 'cert-kid-123')
        self.assertEqual(result.cert_name, 'test-cert')
        self.assertEqual(result.created_at, self.now)
        self.assertEqual(result.assigned_at, self.now)
        self.assertIsNone(result.revoked_at)

    def test_cert_profile_from_orm_with_pending_state(self):
        cert_orm = MagicMock(spec=CertORM)
        cert_orm.id = uuid4()
        cert_orm.state = CertState.PENDING
        cert_orm.public_cert_pem = 'cert-pem'
        cert_orm.thumbprint_sha256 = 'thumbprint'
        cert_orm.not_before = self.now
        cert_orm.not_after = self.now
        cert_orm.cert_kid = 'cert-kid'
        cert_orm.cert_name = 'cert-name'
        cert_orm.created_at = self.now
        cert_orm.assigned_at = None
        cert_orm.revoked_at = None

        result = cert_profile_from_orm(cert_orm)

        self.assertEqual(result.state, CertState.PENDING)
        self.assertIsNone(result.assigned_at)
        self.assertIsNone(result.revoked_at)

    def test_cert_profile_from_orm_with_revoked_state(self):
        revoked_time = datetime.utcnow()

        cert_orm = MagicMock(spec=CertORM)
        cert_orm.id = uuid4()
        cert_orm.state = CertState.REVOKED
        cert_orm.public_cert_pem = 'cert-pem'
        cert_orm.thumbprint_sha256 = 'thumbprint'
        cert_orm.not_before = self.now
        cert_orm.not_after = self.now
        cert_orm.cert_kid = 'cert-kid'
        cert_orm.cert_name = 'cert-name'
        cert_orm.created_at = self.now
        cert_orm.assigned_at = self.now
        cert_orm.revoked_at = revoked_time

        result = cert_profile_from_orm(cert_orm)

        self.assertEqual(result.state, CertState.REVOKED)
        self.assertEqual(result.revoked_at, revoked_time)

    def test_cert_profile_from_orm_with_all_optional_fields_none(self):
        cert_orm = MagicMock(spec=CertORM)
        cert_orm.id = uuid4()
        cert_orm.state = CertState.PENDING
        cert_orm.public_cert_pem = 'cert-pem'
        cert_orm.thumbprint_sha256 = 'thumbprint'
        cert_orm.not_before = self.now
        cert_orm.not_after = self.now
        cert_orm.cert_kid = 'cert-kid'
        cert_orm.cert_name = 'cert-name'
        cert_orm.created_at = self.now
        cert_orm.assigned_at = None
        cert_orm.revoked_at = None

        result = cert_profile_from_orm(cert_orm)

        self.assertIsNone(result.assigned_at)
        self.assertIsNone(result.revoked_at)

    def test_cert_profile_from_orm_preserves_timestamps(self):
        created_time = datetime(2024, 1, 1, 10, 0, 0)
        assigned_time = datetime(2024, 1, 2, 11, 0, 0)
        not_before_time = datetime(2024, 1, 1, 0, 0, 0)
        not_after_time = datetime(2025, 1, 1, 0, 0, 0)

        cert_orm = MagicMock(spec=CertORM)
        cert_orm.id = uuid4()
        cert_orm.state = CertState.ACTIVE
        cert_orm.public_cert_pem = 'cert-pem'
        cert_orm.thumbprint_sha256 = 'thumbprint'
        cert_orm.not_before = not_before_time
        cert_orm.not_after = not_after_time
        cert_orm.cert_kid = 'cert-kid'
        cert_orm.cert_name = 'cert-name'
        cert_orm.created_at = created_time
        cert_orm.assigned_at = assigned_time
        cert_orm.revoked_at = None

        result = cert_profile_from_orm(cert_orm)

        self.assertEqual(result.created_at, created_time)
        self.assertEqual(result.assigned_at, assigned_time)
        self.assertEqual(result.not_before, not_before_time)
        self.assertEqual(result.not_after, not_after_time)

    def test_cert_create_from_dto_with_minimum_validity(self):
        cert_create_request = CertCreateRequest(
            purpose='test',
            key_size=2048,
            validity_in_months=1
        )

        result = cert_create_from_dto(cert_create_request)

        self.assertEqual(result.validity_in_months, 1)

    def test_cert_create_from_dto_with_maximum_validity(self):
        cert_create_request = CertCreateRequest(
            purpose='test',
            key_size=2048,
            validity_in_months=120
        )

        result = cert_create_from_dto(cert_create_request)

        self.assertEqual(result.validity_in_months, 120)

    def test_orm_from_cert_with_special_characters_in_cert_name(self):
        cert = Cert(
            cert_kid='cert-kid-123',
            cert_name='cert-name-with-special-chars-@#$',
            public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
            thumbprint_sha256='thumbprint',
            not_before=self.now,
            not_after=self.now
        )

        result = orm_from_cert(
            organization_id=self.organization_id,
            user_id=self.user_id,
            cert=cert
        )

        self.assertEqual(result.cert_name, 'cert-name-with-special-chars-@#$')

    def test_orm_from_cert_with_long_thumbprint(self):
        long_thumbprint = 'a' * 64

        cert = Cert(
            cert_kid='cert-kid',
            cert_name='cert-name',
            public_cert_pem='cert-pem',
            thumbprint_sha256=long_thumbprint,
            not_before=self.now,
            not_after=self.now
        )

        result = orm_from_cert(
            organization_id=self.organization_id,
            user_id=self.user_id,
            cert=cert
        )

        self.assertEqual(result.thumbprint_sha256, long_thumbprint)
        self.assertEqual(len(result.thumbprint_sha256), 64)

    def test_cert_profile_from_orm_with_multiple_states(self):
        states = [CertState.PENDING, CertState.ACTIVE, CertState.REVOKED]

        for state in states:
            cert_orm = MagicMock(spec=CertORM)
            cert_orm.id = uuid4()
            cert_orm.state = state
            cert_orm.public_cert_pem = 'cert-pem'
            cert_orm.thumbprint_sha256 = 'thumbprint'
            cert_orm.not_before = self.now
            cert_orm.not_after = self.now
            cert_orm.cert_kid = 'cert-kid'
            cert_orm.cert_name = 'cert-name'
            cert_orm.created_at = self.now
            cert_orm.assigned_at = self.now if state != CertState.PENDING else None
            cert_orm.revoked_at = self.now if state == CertState.REVOKED else None

            result = cert_profile_from_orm(cert_orm)

            self.assertEqual(result.state, state)

    def test_orm_from_cert_maintains_cert_validity_period(self):
        not_before = datetime(2024, 1, 1, 0, 0, 0)
        not_after = datetime(2025, 1, 1, 0, 0, 0)

        cert = Cert(
            cert_kid='cert-kid',
            cert_name='cert-name',
            public_cert_pem='cert-pem',
            thumbprint_sha256='thumbprint',
            not_before=not_before,
            not_after=not_after
        )

        result = orm_from_cert(
            organization_id=self.organization_id,
            user_id=self.user_id,
            cert=cert
        )

        self.assertEqual(result.not_before, not_before)
        self.assertEqual(result.not_after, not_after)
        validity_period = (result.not_after - result.not_before).days
        self.assertEqual(validity_period, 366)