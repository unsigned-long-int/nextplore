import uuid

from sqlalchemy import JSON, TIMESTAMP, Column, Text, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class VectorORM(Base):
    __tablename__ = "datastore_vectors"
    __table_args__ = {"schema": "vector"}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    datastore_id = Column(UUID(as_uuid=True), nullable=False)
    qdrant_vector_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    schema_name = Column(Text, nullable=False)
    table_name = Column(Text, nullable=False)
    table_meta = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
