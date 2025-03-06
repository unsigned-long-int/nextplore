from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

from .table_descriptor import TableDescriptor


@dataclass
class SchemaDescriptor:
    tables: Optional[Dict[str, TableDescriptor]] = field(default_factory=dict)

    def __repr__(self) -> str:
        descriptor: List[str] = [
            f'table_name={table_name}: column_names={repr(table.column_names)}'
            for table_name, table in self.tables.items()
        ]
        return ' | '.join(descriptor)
