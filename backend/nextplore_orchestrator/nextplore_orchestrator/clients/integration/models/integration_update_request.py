
from pydantic import BaseModel


class IntegrationUpdateRequest(BaseModel):
    connection_name: str | None
    host: str | None
    port: int | None
    database_name: str | None
    autosync_on: bool | None
