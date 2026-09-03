from pydantic import UUID4, BaseModel


class TableMeta(BaseModel):
    integration_id: UUID4
    schema_name: str
    table_name: str
    column_names: list[str]


class VectorMetaResponse(BaseModel):
    integration_id: UUID4
    schema_name: str
    table_name: str
    table_meta: TableMeta
