from typing import Optional
from pydantic import BaseModel, UUID4, Field

from .cloud import Cloud
from .auth import Auth
from .db import DB


class IntegrationProfile(BaseModel):
    id: UUID4
    auth: Auth
    cloud: Cloud
    db: DB
    connection_name: str
    database_name: str
    host: str
    port: Optional[int] = Field(default=None)
    autosync_on: bool = Field(default=True)
