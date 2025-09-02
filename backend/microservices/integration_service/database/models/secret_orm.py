import uuid
from sqlalchemy import Column, Text, TIMESTAMP, func, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, BYTEA, JSONB

from .base import Base
from .integration_orm import IntegrationORM


class SecretORM(Base):
    __tablename__ = 'integrations'
    __table_args__ = {'schema': 'integration'}

    id = Column(UUID(as_uuid=True),  primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    integration_id = Column(UUID(as_uuid=True), ForeignKey(IntegrationORM.id), nullable=False)
    secret_type = Column(Enum('username', 'password', 'secret', 'aws_role_arn', 'aws_external_id', 'snowflake_private_key'), nullable=False)
    ciphertext = Column(BYTEA, nullable=False)
    nonce = Column(BYTEA, nullable=False)
    tag = Column(BYTEA, nullable=False)
    wrapped_dek = Column(BYTEA, nullable=False)
    kek_kid = Column(Text, nullable=False)
    enc_alg = Column(Text, nullable=False, default='AES-256-GCM')
    wrap_alg = Column(Text, nullable=False, default='RSA-OAEP-256')
    aad = Column(JSONB, nullable=False)
    encoding = Column(Text, nullable=False, default='utf8')
    version = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_accessed_at = Column(TIMESTAMP, nullable=True)
