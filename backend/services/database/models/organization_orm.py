import uuid
from sqlalchemy import Column, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base

class OrganizationORM(Base):
    __tablename__ = 'organizations'
    __table_args__ = {'schema': 'auth'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    azure_tenant_id = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    domain = Column(Text, nullable=False)
    plan = Column(Text, nullable=True, default='free')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    