import uuid
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from .base import Base
from .integration_orm import IntegrationORM


class VectorORM(Base):
    __tablename__ = 'vectors'
    __table_args__ = {'schema': 'embeddings'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey(IntegrationORM.id))
    schema_name = Column(Text, unique=True, nullable=False)
    table_name = Column(Text, unique=True, nullable=False)
    table_meta = Column(JSON, unique=True, nullable=False)
    vector = Column(Vector, unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
