import uuid

from sqlalchemy import Column, Text, TIMESTAMP, Integer, func
from sqlalchemy.dialects.postgresql import UUID, BYTEA

from .base import Base

class UserLlmORM(Base):
    __tablename__ = 'user_llm'
    __table_args__ = {'schema': 'integration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    api_base = Column(Text, nullable=False)
    model_id = Column(Text, nullable=False)
    label = Column(Text, nullable=False)
    max_tokens = Column(Integer, nullable=False)
    encrypted_connection_params = Column(BYTEA, nullable=False)
    nonce = Column(BYTEA, nullable=False)
    tag = Column(BYTEA, nullable=False)
    wrapped_dek = Column(BYTEA, nullable=False)
    enc_alg = Column(Text, nullable=False, default='AES-256-GCM')
    wrap_alg = Column(Text, nullable=False, default='RSA-OAEP-256')
    encoding = Column(Text, nullable=False, default='utf8')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    kek_kid = Column(Text, nullable=False)
