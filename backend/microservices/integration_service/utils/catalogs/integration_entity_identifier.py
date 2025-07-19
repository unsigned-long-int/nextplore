from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class IntegrationEntityIdentifier:
    integration_id: UUID
