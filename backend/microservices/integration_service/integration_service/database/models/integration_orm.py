import uuid
from sqlalchemy import Column, Text, Boolean, TIMESTAMP, Integer, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from svc_integration_contracts.models import DB, Auth, Cloud

from .base import Base


class IntegrationORM(Base):
    __tablename__ = 'integrations'
    __table_args__ = {'schema': 'integration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    auth = Column(
        Enum(
            Auth,
            name='auth',
            schema='integration',
            native_enum=True,
            create_type=False,
            validate_strings=True
        ),
        nullable=False
    )
    cloud = Column(
        Enum(
        Cloud,
            name='cloud',
            schema='integration',
            native_enum=True,
            create_type=False,
            validate_strings=True
        ),
        nullable=False
    )
    db = Column(
        Enum(
        DB,
            name='db',
            schema='integration',
            native_enum=True,
            create_type=False,
            validate_strings=True
        ),
        nullable=False
    )
    connection_name = Column(Text, nullable=False)
    host = Column(Text, nullable=False)
    port = Column(Integer, nullable=True)
    database_name = Column(Text, nullable=False)
    warehouse = Column(Text, nullable=True)
    tenant_id = Column(Text, nullable=True)
    client_id = Column(Text, nullable=True)
    region = Column(Text, nullable=True)
    azure_cert_kid = Column(Text, nullable=True)
    azure_cert_name = Column(Text, nullable=True)
    azure_public_key_pem = Column(Text, nullable=True)
    snowflake_public_key_pem = Column(Text, nullable=True)
    kek_kid = Column(Text, nullable=False)
    autosync_on = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
