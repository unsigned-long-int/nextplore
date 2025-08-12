from pydantic import BaseModel, UUID4


class PreparedIntegrationGetRequest(BaseModel):
    user_id: UUID4
    organization_id: UUID4
