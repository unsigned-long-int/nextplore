from typing import NamedTuple


class DatabaseInspectionFilter(NamedTuple):
    schema_name: str
    table_name: str
