from dataclasses import dataclass, field

from sqlalchemy.engine.interfaces import (
    ReflectedColumn,
    ReflectedForeignKeyConstraint,
    ReflectedIndex,
    ReflectedPrimaryKeyConstraint,
    ReflectedTableComment,
)

from .datastore_entity_identifier import DataStoreEntityIdentifier


@dataclass(frozen=True)
class TableCatalog(DataStoreEntityIdentifier):
    name: str
    columns: list[ReflectedColumn] | None = field(default_factory=list)
    primary_keys: ReflectedPrimaryKeyConstraint | None = field(default=None)
    foreign_keys: list[ReflectedForeignKeyConstraint] | None = field(
        default_factory=list
    )
    indexes: list[ReflectedIndex] | None = field(default_factory=list)
    table_comment: ReflectedTableComment | None = field(default=None)

    @property
    def column_names(self) -> list[str]:
        return [column["name"] for column in self.columns]
