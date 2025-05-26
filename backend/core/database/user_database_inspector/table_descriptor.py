from dataclasses import dataclass
from typing import List

from sqlalchemy.engine.interfaces import (
    ReflectedColumn,
    ReflectedPrimaryKeyConstraint,
    ReflectedForeignKeyConstraint,
    ReflectedIndex,
    ReflectedTableComment
)


class ReflectedColumnMissing(Exception):
    pass


@dataclass
class TableDescriptor:
    columns: List[ReflectedColumn]
    primary_keys: ReflectedPrimaryKeyConstraint
    foreign_keys: List[ReflectedForeignKeyConstraint]
    indexes: List[ReflectedIndex]
    table_comment: ReflectedTableComment

    @property
    def column_names(self) -> List[str]:
        return [column['name'] for column in self.columns]

    def dispatch_reflected_column(
            self,
            column_name: str
    ) -> ReflectedColumn:
        for reflected_column in self.columns:
            if reflected_column['name'] == column_name:
                return reflected_column

        message = f'Column name: {column_name} not found in {repr(self)}'
        raise ReflectedColumnMissing(message)
