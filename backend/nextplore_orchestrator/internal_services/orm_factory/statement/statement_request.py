from dataclasses import dataclass
from typing import List, Dict


@dataclass(frozen=True)
class StatementRequest:
    orm_model: type
    integration: str
    column_names: List[str]
    column_aggregates: List[Dict[str, str]]
    column_filters: List[Dict[str, str | int]]
    