import uuid
from sqlalchemy import Column, Text, TIMESTAMP, func, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, BYTEA

from integration_service.domain.models.secret import SecretType
from .base import Base
from .datastore_orm import DataStoreORM


class SecretORM(Base):
    __tablename__ = 'datastore_secrets'
    __table_args__ = {'schema': 'integration'}

    id = Column(UUID(as_uuid=True),  primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    datastore_id = Column(UUID(as_uuid=True), ForeignKey(DataStoreORM.id), nullable=False)
    secret_type = Column(
        Enum(
            SecretType,
            name='secret_type',
            schema='integration',
            native_enum=True,
            create_type=False,
            validate_strings=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls]
        ),
        nullable=False
    )
    ciphertext = Column(BYTEA, nullable=False)
    nonce = Column(BYTEA, nullable=False)
    tag = Column(BYTEA, nullable=False)
    wrapped_dek = Column(BYTEA, nullable=False)
    enc_alg = Column(Text, nullable=False, default='AES-256-GCM')
    wrap_alg = Column(Text, nullable=False, default='RSA-OAEP-256')
    encoding = Column(Text, nullable=False, default='utf8')
    version = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_accessed_at = Column(TIMESTAMP, nullable=True)
