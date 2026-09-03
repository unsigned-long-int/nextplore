from pydantic import UUID4, BaseModel


class UserProfile(BaseModel):
    id: UUID4
    email: str
    name: str
    organization: str
    organization_id: UUID4
