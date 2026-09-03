from pydantic import UUID4, BaseModel


class IntegrationStatsResponse(BaseModel):
    integration_ids: list[UUID4]
    integration_count: int
