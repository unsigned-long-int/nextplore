import uuid
from sqlalchemy import Column, ForeignKey, Text, CHAR, TIMESTAMP, func, Enum, text
from sqlalchemy.dialects.postgresql import UUID

from integration_service.domain.models.cert import CertState
from .base import Base
from .integration_orm import IntegrationORM



class CertORM(Base):
    __tablename__ = 'certificates'
    __table_args__ = {'schema': 'integration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    integration_id = Column(UUID(as_uuid=True), ForeignKey(IntegrationORM.id), nullable=True)
    state = Column(
        Enum(
            CertState,
            name='cert_state',
            schema='integration',
            native_enum=True,
            create_type=False,
            validate_strings=True
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
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    assigned_at = Column(TIMESTAMP(timezone=True), nullable=True)
    activated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)
