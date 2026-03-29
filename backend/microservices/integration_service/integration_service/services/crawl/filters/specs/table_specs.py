from typing import Dict, Set
from uuid import UUID

from integration_service.services.crawl.filters.logic import Specification
from integration_service.services.crawl.catalogs import TableCatalog


class TableNameSpec(Specification):
    def __init__(self, allowed_datastore_tables: Dict[UUID, Set[str]]) -> None:
        self.allowed = allowed_datastore_tables

    def is_satisfied_by(self, candidate: TableCatalog) -> bool:
        return candidate.name in self.allowed.get(candidate.datastore_id, set())
    