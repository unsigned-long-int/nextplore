from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class User:
    azure_user_id: str
    email: str
    name: str
    organization_id: UUID
    sub: str
    role: str
