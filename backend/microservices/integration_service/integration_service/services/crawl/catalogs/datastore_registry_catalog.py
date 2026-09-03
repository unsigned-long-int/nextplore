from dataclasses import dataclass, field
from typing import ClassVar
from uuid import UUID

from .datastore_catalog import DataStoreCatalog


@dataclass(frozen=True)
class DataStoreRegistryCatalog:
    filter_op_enum: ClassVar[list[str]] = [
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
    agg_funcs_enum: ClassVar[list[str]] = ["sum", "avg", "min", "max", "count"]

    datastores: tuple[DataStoreCatalog] = field(default_factory=tuple)

    @property
    def datastores_enum(self) -> list[str]:
        return [str(datastore.id) for datastore in self.datastores]

    @property
    def table_metas(self) -> list[dict[str, UUID | str | list[str]]]:
        return [
            {
                "datastore_id": datastore.id,
                "schema_name": schema.name,
                "table_name": table.name,
                "column_names": table.column_names,
            }
            for datastore in self.datastores
            for schema in datastore.schemas
            for table in schema.tables
        ]

    @property
    def schemas_enum(self) -> list[str]:
        return [
            schema.name for datastore in self.datastores for schema in datastore.schemas
        ]

    @property
    def tables_enum(self) -> list[str]:
        return [
            table.name
            for datastore in self.datastores
            for schema in datastore.schemas
            for table in schema.tables
        ]

    @property
    def columns_enum(self) -> list[str]:
        return [
            column
            for datastore in self.datastores
            for schema in datastore.schemas
            for table in schema.tables
            for column in table.column_names
        ]

    def __repr__(self) -> str:
        descriptor: list[str] = [
            f"datastore_id={datastore.id}: [{datastore!r}]"
            for datastore in self.datastores
        ]
        return " | ".join(descriptor)
