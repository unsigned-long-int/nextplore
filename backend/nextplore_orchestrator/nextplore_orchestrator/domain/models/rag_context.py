from dataclasses import dataclass, field


@dataclass(frozen=True)
class RagContext:
    datastore_registry_repr: str
    datastores_enum: list[str]
    schemas_enum: list[str]
    tables_enum: list[str]
    columns_enum: list[str]
    table_columns_registry: dict[str, dict[str, dict[str, list[str]]]]
    filter_op_enum: list[str] = field(
        default_factory=lambda: [
            "==",
            "!=",
            ">",
            "<",
            ">=",
            "<=",
            "like",
            "not like",
            "in",
        ]
    )
    agg_funcs_enum: list[str] = field(
        default_factory=lambda: ["sum", "avg", "min", "max", "count"]
    )
