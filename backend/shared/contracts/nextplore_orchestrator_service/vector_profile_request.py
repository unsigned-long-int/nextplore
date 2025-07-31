from pydantic import BaseModel, UUID4


class VectorProfileRequest(BaseModel):
    integration_id: UUID4
    