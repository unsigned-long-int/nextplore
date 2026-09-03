from uuid import UUID

from integration_service.services.crawl.catalogs import SchemaCatalog
from integration_service.services.crawl.filters.logic import Specification


class SchemaNameSpec(Specification):
    def __init__(self, allowed_datastore_schemas: dict[UUID, set[str]]) -> None:
        self.allowed = allowed_datastore_schemas

    def is_satisfied_by(self, candidate: SchemaCatalog) -> bool:
        return candidate.name in self.allowed.get(candidate.integration_id, set())
