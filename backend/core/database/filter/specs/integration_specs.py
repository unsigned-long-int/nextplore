from typing import Set
from uuid import UUID

from core.database.filter.logic import Specification
from core.database.catalogs import IntegrationCatalog


class IntegrationIdSpec(Specification):
    def __init__(self, integration_ids: Set[UUID]) -> None:
        self.allowed = integration_ids

    def is_satisfied_by(self, candidate: IntegrationCatalog) -> bool:
        return candidate.id in self.allowed
    