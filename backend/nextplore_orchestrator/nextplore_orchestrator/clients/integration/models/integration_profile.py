
from pydantic import UUID4, BaseModel, Field

from .auth import Auth
from .cloud import Cloud
from .db import DB


class IntegrationProfile(BaseModel):
    id: UUID4
    auth: Auth
    cloud: Cloud
    db: DB
    connection_name: str
    database_name: str
    host: str
    port: int | None = Field(default=None)
    autosync_on: bool = Field(default=True)
