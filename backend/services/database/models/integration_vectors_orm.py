from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey

from .base import Base
from .integration_orm import IntegrationORM
from .vector_orm import VectorORM


class IntegrationVectorsORM(Base):
    __tablename__ = 'integration_vectors'
    __table_args__ = {'schema': 'embeddings'}

    integration_id = Column(UUID(as_uuid=True), ForeignKey(IntegrationORM.id), primary_key=True)
    vector_id = Column(UUID(as_uuid=True), ForeignKey(VectorORM.id), primary_key=True)
