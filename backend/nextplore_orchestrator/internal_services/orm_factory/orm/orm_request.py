from dataclasses import dataclass


@dataclass(frozen=True)
class ORMRequest:
    integration: str
    schema_name: str
    class_name: str
    table_name: str
    connection_string: str
    