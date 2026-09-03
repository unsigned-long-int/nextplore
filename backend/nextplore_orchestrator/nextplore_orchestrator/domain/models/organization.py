from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Organization:
    azure_tenant_id: str
    name: str
    domain: str
    plan: str = field(default="standard")
    status: str = field(default="active")
    id: UUID | None = field(default=None)
    onboarding_request_id: UUID | None = field(default=None)
    activated_at: datetime | None = field(default=None)
    suspended_at: datetime | None = field(default=None)
    suspend_reason: str | None = field(default=False)
