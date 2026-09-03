from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TableMeta:
    datastore_id: UUID
    schema_name: str
    table_name: str
    column_names: list[str]
