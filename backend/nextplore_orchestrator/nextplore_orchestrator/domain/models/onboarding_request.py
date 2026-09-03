from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class OnboardingRequest:
    company_name: str
    email_domain: str
    contact_email: str
    plan: str = field(default="standard")
    email_verified: bool = field(default=False)
    status: str = field(default="pending")
    id: UUID | None = field(default=None)
    verification_token: str | None = field(default=None)
    verified_at: datetime | None = field(default=None)
    reviewed_by: str | None = field(default=None)
    review_note: str | None = field(default=None)
    reviewed_at: datetime | None = field(default=None)
    outbox_mail_id: UUID | None = field(default=None)
    verification_token_expires_at: datetime | None = field(default=None)
