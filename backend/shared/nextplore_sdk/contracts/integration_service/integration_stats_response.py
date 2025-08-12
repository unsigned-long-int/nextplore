from typing import List
from pydantic import BaseModel, UUID4


class IntegrationStatsResponse(BaseModel):
    integration_ids: List[UUID4]
    integration_count: int