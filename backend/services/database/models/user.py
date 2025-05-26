import uuid
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from .organizaton import Organization

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False)
    name = Column(Text)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(Organization.id))
    sub = Column(Text, unique=True)
    role = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    #organization = relationship('Organization', backref='users')