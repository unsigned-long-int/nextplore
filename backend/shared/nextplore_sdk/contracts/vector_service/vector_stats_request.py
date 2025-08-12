from pydantic import BaseModel, UUID4


class VectorStatsRequest(BaseModel):
    organization_id: UUID4
    user_id: UUID4
