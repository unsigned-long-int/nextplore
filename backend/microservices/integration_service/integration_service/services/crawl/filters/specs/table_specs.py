from uuid import UUID

from integration_service.services.crawl.catalogs import TableCatalog
from integration_service.services.crawl.filters.logic import Specification


class TableNameSpec(Specification):
    def __init__(self, allowed_datastore_tables: dict[UUID, set[str]]) -> None:
        self.allowed = allowed_datastore_tables

    def is_satisfied_by(self, candidate: TableCatalog) -> bool:
        return candidate.name in self.allowed.get(candidate.datastore_id, set())
