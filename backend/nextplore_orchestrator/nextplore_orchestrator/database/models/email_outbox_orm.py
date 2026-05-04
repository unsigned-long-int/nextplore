import uuid

from sqlalchemy import Column, Text, Integer, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class EmailOutboxORM(Base):
    __tablename__ = 'email_outbox'
    __table_args__ = {'schema': 'notification'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    html = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default='pending')
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    last_error = Column(Text, nullable=True)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())