from dataclasses import dataclass, field
from uuid import UUID

from svc_integration_contracts.models import DB, Auth, Cloud


@dataclass(frozen=True)
class DataStoreProfile:
    id: UUID
    auth: Auth
    cloud: Cloud
    db: DB
    connection_name: str
    database_name: str
    host: str
    port: int | None = field(default=None)
    autosync_on: bool | None = field(default=True)
