from pydantic import BaseModel, UUID4
from typing import List


class TableMeta(BaseModel):
    integration_id: UUID4
    schema_name: str
    table_name: str
    column_names: List[str]


class VectorMetaResponse(BaseModel):
    integration_id: UUID4
    schema_name: str
    table_name: str
    table_meta: TableMeta
