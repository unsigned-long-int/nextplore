from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserIdentity:
    organization_id: UUID
    user_id: UUID
