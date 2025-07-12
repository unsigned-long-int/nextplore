from pydantic import BaseModel, UUID4 


class InitialInspectionRequest(BaseModel):
    integration_id: UUID4
