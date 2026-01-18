from uuid import UUID
from typing import Optional
from dataclasses import dataclass, field
from svc_integration_contracts.models import DB, Auth, Cloud


@dataclass(frozen=True)
class IntegrationProfile:
    id: UUID
    auth: Auth
    cloud: Cloud
    db: DB
    connection_name: str
    database_name: str
    host: str
    port: Optional[int] = field(default=None)
    autosync_on: Optional[bool] = field(default=True)
