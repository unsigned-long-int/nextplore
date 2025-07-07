from pydantic import BaseModel, UUID4


class VectorMetadataRequest(BaseModel):
    integration_id: UUID4
    