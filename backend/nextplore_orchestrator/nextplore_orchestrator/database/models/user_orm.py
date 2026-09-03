import uuid
from typing import ClassVar

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base
from .organization_orm import OrganizationORM


class UserORM(Base):
    __tablename__: ClassVar = "users"
    __table_args__: ClassVar = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    azure_user_id = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    name = Column(Text)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(OrganizationORM.id))
    sub = Column(Text, unique=True)
    role = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
