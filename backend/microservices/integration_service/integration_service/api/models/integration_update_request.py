from typing import Optional
from pydantic import BaseModel


class IntegrationUpdateRequest(BaseModel):
    connection_name: Optional[str]
    host: Optional[str]
    port: Optional[int]
    database_name: Optional[str]
    autosync_on: Optional[bool]
