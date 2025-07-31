from pydantic import BaseModel, UUID4


class UserProfile(BaseModel):
    id: UUID4
    email: str
    name: str
    organization: str
    organization_id: UUID4