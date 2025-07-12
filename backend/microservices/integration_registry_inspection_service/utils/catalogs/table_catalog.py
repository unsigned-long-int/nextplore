from dataclasses import dataclass, field
from typing import List, Set, Optional

from sqlalchemy.engine.interfaces import (
    ReflectedColumn,
    ReflectedPrimaryKeyConstraint,
    ReflectedForeignKeyConstraint,
    ReflectedIndex,
    ReflectedTableComment
)
from .integration_entity_identifier import IntegrationEntityIdentifier


@dataclass(frozen=True)
class TableCatalog(IntegrationEntityIdentifier):
    name: str
    columns: Optional[Set[ReflectedColumn]] = field(default_factory=set)
    primary_keys: Optional[ReflectedPrimaryKeyConstraint] = field(default=None)
    foreign_keys: Optional[Set[ReflectedForeignKeyConstraint]] = field(default_factory=set)
    indexes: Optional[Set[ReflectedIndex]] = field(default_factory=set)
    table_comment: Optional[ReflectedTableComment] = field(default=None)

    @property
    def column_names(self) -> List[str]:
        return [column['name'] for column in self.columns]
