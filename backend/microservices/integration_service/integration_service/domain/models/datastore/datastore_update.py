from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DataStoreUpdate:
    connection_name: str | None
    host: str | None
    port: int | None
    database_name: str | None
    autosync_on: bool | None

    @property
    def update_args(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}
