from dataclasses import dataclass


@dataclass(frozen=True)
class ORMContext:
    datastore: str
    schema_name: str
    class_name: str
    table_name: str
    column_names: list[str]
    column_aggregates: list[dict[str, str]]
    column_filters: list[dict[str, str | int]]
