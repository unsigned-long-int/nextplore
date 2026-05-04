from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from datetime import datetime


@dataclass(frozen=True)
class OnboardingRequest:
    company_name: str
    email_domain: str
    contact_email: str
    plan: str = field(default='standard')
    email_verified: bool = field(default=False)
    status: str = field(default="pending")
    id: Optional[UUID] = field(default=None)
    verification_token: Optional[str] = field(default=None)
    verified_at: Optional[datetime] =  field(default=None)
    reviewed_by: Optional[str] =  field(default=None)
    review_note: Optional[str] =  field(default=None)
    reviewed_at: Optional[datetime] = field(default=None)
    outbox_mail_id: Optional[UUID] = field(default=None)
    verification_token_expires_at: Optional[datetime] = field(default=None)

