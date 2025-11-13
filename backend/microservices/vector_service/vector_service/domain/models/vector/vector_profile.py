from uuid import UUID
from dataclasses import dataclass

from .table_meta import TableMeta


@dataclass(frozen=True)
class VectorProfile:
    integration_id: UUID
    schema_name: str
    table_name: str
    table_meta: TableMeta
    