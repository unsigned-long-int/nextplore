from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.engine.interfaces import (
    ReflectedColumn,
    ReflectedPrimaryKeyConstraint,
    ReflectedForeignKeyConstraint,
    ReflectedIndex,
    ReflectedTableComment
)
from .datastore_entity_identifier import DataStoreEntityIdentifier


@dataclass(frozen=True)
class TableCatalog(DataStoreEntityIdentifier):
    name: str
    columns: Optional[List[ReflectedColumn]] = field(default_factory=list)
    primary_keys: Optional[ReflectedPrimaryKeyConstraint] = field(default=None)
    foreign_keys: Optional[List[ReflectedForeignKeyConstraint]] = field(default_factory=list)
    indexes: Optional[List[ReflectedIndex]] = field(default_factory=list)
    table_comment: Optional[ReflectedTableComment] = field(default=None)

    @property
    def column_names(self) -> List[str]:
        return [column['name'] for column in self.columns]
