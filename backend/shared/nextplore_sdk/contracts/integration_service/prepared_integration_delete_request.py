from pydantic import BaseModel, UUID4


class PreparedIntegrationDeleteRequest(BaseModel):
    integration_id: str
    user_id: UUID4
    organization_id: UUID4
