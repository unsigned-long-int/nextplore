import uuid
from sqlalchemy import Column, Text, TIMESTAMP, func, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID

from .organizaton import Organization
from .user import User
from .base import Base

class Integration(Base):
    __tablename__ = 'integrations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(Organization.id))
    user_id = Column(UUID(as_uuid=True), ForeignKey(User.id))
    service_type = Column(Text, nullable=False)
    auth_method = Column(Text, nullable=False)
    connection_name = Column(Text, nullable=False)
    host = Column(Text, nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(Text, nullable=False)
    encrypted_username = Column(Text, nullable=True)
    encrypted_password = Column(Text, nullable=True)
    encrypted_kerberos_principal = Column(Text, nullable=True)
    encrypted_windows_domain = Column(Text, nullable=True)
    encrypted_extra_options = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
