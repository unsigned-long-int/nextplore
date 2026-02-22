from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class IntegrationUpdate:
    connection_name: Optional[str]
    host: Optional[str]
    port: Optional[int]
    database_name: Optional[str]
    autosync_on: Optional[bool]


    @property
    def update_args(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

