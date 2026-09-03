import uuid
from typing import ClassVar

from sqlalchemy import TIMESTAMP, Boolean, Column, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class OnboardingRequestORM(Base):
    __tablename__: ClassVar = "onboarding_requests"
    __table_args__: ClassVar = (
        UniqueConstraint("domain", name="onboarding_requests_domain_key"),
        {"schema": "auth"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(Text, nullable=False)
    domain = Column(Text, nullable=False)
    contact_email = Column(Text, nullable=False)
    plan = Column(Text, nullable=False, default="standard")
    status = Column(Text, nullable=False, default="pending")
    email_verified = Column(Boolean, nullable=False, default=False)
    verification_token = Column(Text, nullable=False)
    verified_at = Column(TIMESTAMP(timezone=True), nullable=True)
    reviewed_by = Column(Text, nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    outbox_mail_id = Column(UUID(as_uuid=True), nullable=True)
    verification_token_expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
