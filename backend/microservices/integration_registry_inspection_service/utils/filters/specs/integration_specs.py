from typing import Set
from uuid import UUID

from utils.filters.logic import Specification
from utils.catalogs import IntegrationCatalog


class IntegrationIdSpec(Specification):
    def __init__(self, integration_ids: Set[UUID]) -> None:
        self.allowed = integration_ids

    def is_satisfied_by(self, candidate: IntegrationCatalog) -> bool:
        print(candidate.id)
        return candidate.id in self.allowed
    