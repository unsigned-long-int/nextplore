from dataclasses import dataclass, field
from uuid import UUID

from .schema_catalog import SchemaCatalog


@dataclass(frozen=True)
class DataStoreCatalog:
    id: UUID
    schemas: tuple[SchemaCatalog] = field(default_factory=tuple)

    def __repr__(self) -> str:
        descriptor: list[str] = [
            f"schema_name={schema.name}: [{schema!r}]" for schema in self.schemas
        ]
        return " | ".join(descriptor)
