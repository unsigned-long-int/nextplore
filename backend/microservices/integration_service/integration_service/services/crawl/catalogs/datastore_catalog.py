from dataclasses import dataclass, field
from typing import Tuple, List
from uuid import UUID

from .schema_catalog import SchemaCatalog


@dataclass(frozen=True)
class DataStoreCatalog:
    id: UUID
    schemas: Tuple[SchemaCatalog] = field(default_factory=tuple)
    
    def __repr__(self) -> str:
        descriptor: List[str] = [
            f'schema_name={schema.name}: [{repr(schema)}]'
            for schema in self.schemas
        ]
        return ' | '.join(descriptor)
