from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DataStoreEntityIdentifier:
    datastore_id: UUID
