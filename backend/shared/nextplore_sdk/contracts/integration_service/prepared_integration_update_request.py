from typing import Dict
from pydantic import BaseModel, UUID4


class PreparedIntegrationUpdateRequest(BaseModel):
    integration_id: UUID4
    user_id: UUID4
    organization_id: UUID4
    update_args: Dict[str, str | bool | int]
