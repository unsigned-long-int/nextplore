from pydantic import BaseModel, UUID4


class VectorMetadata(BaseModel):
    integration_id: UUID4
    schema_name: str
    table_name: str
    table_meta: str
    