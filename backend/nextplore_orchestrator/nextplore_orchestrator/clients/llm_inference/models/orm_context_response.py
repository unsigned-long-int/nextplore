from typing import List, Dict
from pydantic import BaseModel, UUID4


class ORMContextResponse(BaseModel):
    integration: UUID4
    schema_name: str
    class_name: str
    table_name: str
    column_names: List[str]
    column_aggregates: List[Dict[str, str]]
    column_filters: List[Dict[str, str | int]]
    