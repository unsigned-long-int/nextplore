from uuid import UUID
from typing import List
from dataclasses import dataclass


@dataclass(frozen=True)
class TableMeta:
    integration_id: UUID
    schema_name: str
    table_name: str
    column_names: List[str]
