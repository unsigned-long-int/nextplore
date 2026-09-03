from pydantic import UUID4, BaseModel


class VectorProfileResponse(BaseModel):
    integration_id: UUID4
    schema_name: str
    table_name: str
    table_meta: str
