from pydantic import BaseModel, UUID4


class IntegrationProfile(BaseModel):
    id: UUID4
    service_type: str
    connection_name: str
    database_name: str
    auth_method: str 
    autosync_on: bool