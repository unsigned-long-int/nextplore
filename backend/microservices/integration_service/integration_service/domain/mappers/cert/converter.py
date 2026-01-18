from uuid import UUID
from svc_integration_contracts.models import CertCreateRequest
from nextplore_sdk.encryptor.models.cert import Cert

from integration_service.domain.models.cert import CertCreate, CertProfile
from integration_service.database.models import CertORM


def cert_create_from_dto(cert_create_request: CertCreateRequest) -> CertCreate:
    return CertCreate(
        purpose=cert_create_request.purpose,
        key_size=cert_create_request.key_size,
        validity_in_months=cert_create_request.validity_in_months
    )


def orm_from_cert(
    organization_id: UUID,
    user_id: UUID,
    cert: Cert
) -> CertORM:
    return CertORM(
        organization_id=organization_id,
        user_id=user_id,
        cert_kid=cert.cert_kid,
        cert_name=cert.cert_name,
        public_cert_pem=cert.public_cert_pem,
        thumbprint_sha256=cert.thumbprint_sha256,
        not_before=cert.not_before,
        not_after=cert.not_after,
    )


def cert_profile_from_orm(
    cert_orm: CertORM
) -> CertProfile:
    return CertProfile(
        id=cert_orm.id,
        state=cert_orm.state,
        public_cert_pem=cert_orm.public_cert_pem,
        thumbprint_sha256=cert_orm.thumbprint_sha256,
        not_before=cert_orm.not_before,
        not_after=cert_orm.not_after,
        cert_kid=cert_orm.cert_kid,
        cert_name=cert_orm.cert_name,
        created_at=cert_orm.created_at,
        assigned_at=cert_orm.assigned_at,
        revoked_at=cert_orm.revoked_at
    )
