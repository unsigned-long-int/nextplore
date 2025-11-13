from typing import Set, Dict
from uuid import UUID

from integration_service.services.crawl.filters.logic import Specification
from integration_service.services.crawl.catalogs import SchemaCatalog


class SchemaNameSpec(Specification):
    def __init__(self, allowed_integration_schemas: Dict[UUID, Set[str]]) -> None:
        self.allowed = allowed_integration_schemas

    def is_satisfied_by(self, candidate: SchemaCatalog) -> bool:
        return candidate.name in self.allowed.get(candidate.integration_id, set())
