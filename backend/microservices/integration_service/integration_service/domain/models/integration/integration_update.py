from uuid import UUID
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationUpdate:
    connection_name: Optional[str]
    host: Optional[str]
    port: Optional[int]
    database_name: Optional[str]
    autosync_on: Optional[bool]
