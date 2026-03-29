from dataclasses import dataclass


@dataclass(frozen=True)
class ORMRequest:
    datastore: str
    schema_name: str
    class_name: str
    table_name: str
