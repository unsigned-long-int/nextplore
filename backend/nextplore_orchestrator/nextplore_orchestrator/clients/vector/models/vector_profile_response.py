from pydantic import BaseModel, UUID4


class VectorProfileResponse(BaseModel):
    integration_id: UUID4
    schema_name: str
    table_name: str
    table_meta: str
