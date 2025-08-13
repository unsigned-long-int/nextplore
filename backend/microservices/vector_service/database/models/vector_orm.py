import uuid
from sqlalchemy import Column, Text, TIMESTAMP, JSON, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class VectorORM(Base):
    __tablename__ = 'vectors'
    __table_args__ = {'schema': 'vector'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    integration_id = Column(UUID(as_uuid=True), nullable=False)
    qdrant_vector_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    schema_name = Column(Text, unique=True, nullable=False)
    table_name = Column(Text, unique=True, nullable=False)
    table_meta = Column(JSON, unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
