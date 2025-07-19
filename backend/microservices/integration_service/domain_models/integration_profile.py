from uuid import UUID
from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationProfile:
    id: UUID
    service_type: str
    connection_name: str
    database_name: str
    auth_method: str
    autosync_on: bool
