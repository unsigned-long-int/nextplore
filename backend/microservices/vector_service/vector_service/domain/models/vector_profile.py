from dataclasses import dataclass
from uuid import UUID

from .table_meta import TableMeta


@dataclass(frozen=True)
class VectorProfile:
    datastore_id: UUID
    schema_name: str
    table_name: str
    table_meta: TableMeta
