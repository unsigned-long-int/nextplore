from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ORMRequest:
    orm_model: type
    selected_columns: List[str]
    aggregates: List[Dict[str, str]]
    filters: List[Dict[str, str | int]]
    