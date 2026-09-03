from dataclasses import dataclass, field

from .datastore_entity_identifier import DataStoreEntityIdentifier
from .table_catalog import TableCatalog


@dataclass(frozen=True)
class SchemaCatalog(DataStoreEntityIdentifier):
    name: str
    tables: tuple[TableCatalog, ...] = field(default_factory=tuple)

    def __repr__(self) -> str:
        descriptor: list[str] = [
            f"table_name={table.name}: column_names={table.column_names!r}"
            for table in self.tables
        ]

        return " | ".join(descriptor)
