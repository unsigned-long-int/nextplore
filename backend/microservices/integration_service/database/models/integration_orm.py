import uuid
from enum import Enum
from sqlalchemy import Column, Text, TIMESTAMP, func, Enum, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class IntegrationORM(Base):
    __tablename__ = 'integrations'
    __table_args__ = {'schema': 'integration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    auth = Column(Enum('iam', 'secret', 'cert', 'password_native', 'password_proxy', 'jwt', name='Auth', create_type=False), nullable=False)
    cloud = Column(Enum('aws', 'azure', 'gcp', 'snowflake_managed', name='Cloud', create_type=False), nullable=False)
    db = Column(Enum('mysql', 'sqlserver', 'postgresql', 'snowflake', name='DB', create_type=False), nullable=False)
    connection_name = Column(Text, nullable=False)
    host = Column(Text, nullable=False)
    port = Column(Integer, nullable=True)
    database_name = Column(Text, nullable=False)
    warehouse = Column(Text, nullable=True)
    tenant_id = Column(Text, nullable=True)
    client_id = Column(Text, nullable=True)
    region = Column(Text, nullable=True)
    azure_cert_kid = Column(Text, nullable=True)
    azure_public_key_pem = Column(Text, nullable=True)
    snowflake_public_key_pem = Column(Text, nullable=True)
    autosync_on = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
