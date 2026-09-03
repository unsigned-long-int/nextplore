from dataclasses import dataclass


@dataclass(frozen=True)
class StatementRequest:
    orm_model: type
    datastore: str
    column_names: list[str]
    column_aggregates: list[dict[str, str]]
    column_filters: list[dict[str, str | int]]
