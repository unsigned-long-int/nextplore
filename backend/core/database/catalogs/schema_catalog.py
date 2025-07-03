from dataclasses import dataclass, field
from typing import List, Tuple

from .integration_entity_identifier import IntegrationEntityIdentifier
from .table_catalog import TableCatalog


@dataclass(frozen=True)
class SchemaCatalog(IntegrationEntityIdentifier):
    name: str
    tables: Tuple[TableCatalog] = field(default_factory=tuple)

    def __repr__(self) -> str:
        descriptor: List[str] = [
            f'table_name={table.name}: column_names={repr(table.column_names)}'
            for table in self.tables
        ]

        return ' | '.join(descriptor)