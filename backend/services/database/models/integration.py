import uuid
from sqlalchemy import Column, Text, TIMESTAMP, func, ForeignKey, Integer, LargeBinary, JSON
from sqlalchemy.dialects.postgresql import UUID

from .organizaton import Organization
from .user import User
from .base import Base

class Integration(Base):
    __tablename__ = 'integrations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(Organization.id))
    created_by = Column(UUID(as_uuid=True), ForeignKey(User.id))
    type = Column(Text, nullable=False)
    method = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    host = Column(Text, nullable=True)
    port = Column(Integer, nullable=True)
    database = Column(Text, nullable=True)
    username = Column(Text, nullable=True)
    password_encrypted = Column(LargeBinary, nullable=True)
    api_key_encrypted = Column(LargeBinary, nullable=True)
    kerberos_principal = Column(LargeBinary, nullable=True)
    kerberos_keytab_encrypted = Column(LargeBinary, nullable=True)
    connection_uri = Column(Text, nullable=True)
    extra = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
