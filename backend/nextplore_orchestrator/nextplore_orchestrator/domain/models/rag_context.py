from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class RagContext:
    integration_registry_repr: str
    integrations_enum: List[str]
    schemas_enum: List[str]
    tables_enum: List[str]
    columns_enum: List[str]
    filter_op_enum: List[str] = field(
        default_factory=lambda: ['==', '!=', '>', '<', '>=', '<=', 'like', 'not like', 'in'])
    agg_funcs_enum: List[str] = field(
        default_factory=lambda: ['sum', 'avg', 'min', 'max', 'count'])
