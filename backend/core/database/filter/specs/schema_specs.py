from typing import Set, Dict
from uuid import UUID

from core.database.filter.logic import Specification
from core.database.catalogs import SchemaCatalog


class SchemaNameSpec(Specification):
    def __init__(self, allowed_integration_schemas: Dict[UUID, Set[str]]) -> None:
        self.allowed = allowed_integration_schemas

    def is_satisfied_by(self, candidate: SchemaCatalog) -> bool:
        return candidate.name in self.allowed.get(candidate.integration_id, set())
