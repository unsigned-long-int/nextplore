from uuid import UUID
from typing import Optional
from dataclasses import dataclass, field

from .db import DB
from .auth import Auth
from .cloud import Cloud


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
