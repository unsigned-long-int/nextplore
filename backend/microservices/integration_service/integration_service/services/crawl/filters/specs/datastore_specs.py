from uuid import UUID

from integration_service.services.crawl.catalogs import DataStoreCatalog
from integration_service.services.crawl.filters.logic import Specification


class DataStoreIdSpec(Specification):
    def __init__(self, datastore_ids: set[UUID]) -> None:
        self.allowed = datastore_ids

    def is_satisfied_by(self, candidate: DataStoreCatalog) -> bool:
        return candidate.id in self.allowed
