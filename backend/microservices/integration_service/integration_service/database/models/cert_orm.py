import uuid

from sqlalchemy import (
    CHAR,
    TIMESTAMP,
    Column,
    Enum,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from svc_integration_contracts.models import CertState

from .base import Base
from .datastore_orm import DataStoreORM


class CertORM(Base):
    __tablename__ = "datastore_certificates"
    __table_args__ = (
        Index("idx_certificates_org_user", "organization_id", "user_id"),
        {"schema": "integration"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    datastore_id = Column(
        UUID(as_uuid=True),
        ForeignKey(DataStoreORM.id, name="fk_datastore_certificates_datastore_id"),
        nullable=True,
    )
    state = Column(
        Enum(
            CertState,
            name="cert_state",
            schema="integration",
            native_enum=True,
            create_type=False,
            validate_strings=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        server_default=text("'PENDING'::integration.cert_state"),
    )
    cert_kid = Column(Text, nullable=False)
    cert_name = Column(Text, nullable=False)
    public_cert_pem = Column(Text, nullable=False)
    thumbprint_sha256 = Column(CHAR(64), nullable=False)
    not_before = Column(TIMESTAMP(timezone=True), nullable=False)
    not_after = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    assigned_at = Column(TIMESTAMP(timezone=True), nullable=True)
    activated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)
