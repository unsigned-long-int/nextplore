import uuid

from sqlalchemy import TIMESTAMP, Column, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, UUID

from .base import Base


class UserLlmORM(Base):
    __tablename__ = "user_llm"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            "model_id",
            "api_base",
            name="uq_user_hosted_llm_user_model_endpoint",
        ),
        Index("idx_user_hosted_llm_org_user", "organization_id", "user_id"),
        {"schema": "integration"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    api_base = Column(Text, nullable=False)
    model_id = Column(Text, nullable=False)
    label = Column(Text, nullable=False)
    max_tokens = Column(Integer, nullable=False)
    encrypted_connection_params = Column(BYTEA, nullable=False)
    nonce = Column(BYTEA, nullable=False)
    tag = Column(BYTEA, nullable=False)
    wrapped_dek = Column(BYTEA, nullable=False)
    enc_alg = Column(Text, nullable=False, default="AES-256-GCM")
    wrap_alg = Column(Text, nullable=False, default="RSA-OAEP-256")
    encoding = Column(Text, nullable=False, default="utf8")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    kek_kid = Column(Text, nullable=False)
