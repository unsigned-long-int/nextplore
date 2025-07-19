from pydantic import BaseModel, UUID4 


class InitialCrawlRequest(BaseModel):
    integration_id: UUID4
