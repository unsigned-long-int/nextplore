from typing import Dict, Set
from uuid import UUID

from core.database.filter.logic import Specification
from core.database.catalogs import TableCatalog


class TableNameSpec(Specification):
    def __init__(self, allowed_integration_tables: Dict[UUID, Set[str]]) -> None:
        self.allowed = allowed_integration_tables

    def is_satisfied_by(self, candidate: TableCatalog) -> bool:
        return candidate.name in self.allowed.get(candidate.integration_id, set())
    