from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class Organization:
    azure_tenant_id: str
    name: str
    domain: str
    plan: str = field(default='standard')
    status: str = field(default='active')
    id: Optional[UUID] = field(default=None)
    onboarding_request_id: Optional[UUID] = field(default=None)
    activated_at: Optional[datetime] = field(default=None)
    suspended_at: Optional[datetime] = field(default=None)
    suspend_reason: Optional[str] = field(default=False)

