from dataclasses import dataclass, field
from typing import List, Tuple

from .datastore_entity_identifier import DataStoreEntityIdentifier
from .table_catalog import TableCatalog


@dataclass(frozen=True)
class SchemaCatalog(DataStoreEntityIdentifier):
    name: str
    tables: Tuple[TableCatalog, ...] = field(default_factory=tuple)

    def __repr__(self) -> str:
        descriptor: List[str] = [
            f'table_name={table.name}: column_names={repr(table.column_names)}'
            for table in self.tables
        ]

        return ' | '.join(descriptor)