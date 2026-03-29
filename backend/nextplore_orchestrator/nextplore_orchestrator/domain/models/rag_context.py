from dataclasses import dataclass, field
from typing import List, Dict

@dataclass(frozen=True)
class RagContext:
    datastore_registry_repr: str
    datastores_enum: List[str]
    schemas_enum: List[str]
    tables_enum: List[str]
    columns_enum: List[str]
    table_columns_registry: Dict[str, Dict[str, Dict[str, List[str]]]]
    filter_op_enum: List[str] = field(
        default_factory=lambda: ['==', '!=', '>', '<', '>=', '<=', 'like', 'not like', 'in'])
    agg_funcs_enum: List[str] = field(
        default_factory=lambda: ['sum', 'avg', 'min', 'max', 'count'])
