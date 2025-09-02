from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, BYTEA, JSONB
from sqlalchemy import String, Integer, Text, Column, Enum

from .base import Base

class IntegrationSecretMvORM(Base):
    __tablename__ = 'mv_integration_secrets'
    __table_args__ = {'schema': 'integration'}

    organization_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    integration_id = Column(UUID(as_uuid=True), primary_key=True)
    auth = Column(Enum('iam', 'secret', 'cert', 'password_native', 'password_proxy', 'jwt'), nullable=False)
    cloud = Column(Enum('aws', 'azure', 'gcp', 'snowflake_managed'), nullable=False)
    db = Column(Enum('mysql', 'sqlserver', 'postgresql', 'snowflake'), nullable=False)
    host = Column(Text, nullable=False)
    port = Column(Integer, nullable=True)
    database_name = Column(Text, nullable=True)
    warehouse = Column(Text, nullable=True)
    tenant_id = Column(Text, nullable=True)
    client_id = Column(Text, nullable=True)
    region = Column(Text, nullable=True)
    azure_cert_kid = Column(Text, nullable=True)
    secret_type = Column(Enum('username', 'password', 'secret', 'aws_role_arn', 'aws_external_id', 'snowflake_private_key'), primary_key=True)
    version = Column(Integer, nullable=True)
    ciphertext = Column(BYTEA, nullable=True)
    nonce = Column(BYTEA, nullable=True)
    tag = Column(BYTEA, nullable=True)
    aad = Column(JSONB, nullable=True)
    wrapped_dek = Column(BYTEA, nullable=True)
    kek_kid = Column(Text, nullable=True)
    enc_alg = Column(Text, nullable=True)
    wrap_alg = Column(Text, nullable=True)
    encoding = Column(Text, nullable=True)
