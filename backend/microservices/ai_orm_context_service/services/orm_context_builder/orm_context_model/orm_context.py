from dataclasses import dataclass
from typing import List, Dict


@dataclass(frozen=True)
class ORMContext:
    integration: str
    schema_name: str
    class_name: str
    table_name: str
    column_names: List[str]
    column_aggregates: List[Dict[str, str]]
    column_filters: List[Dict[str, str | int]]

    