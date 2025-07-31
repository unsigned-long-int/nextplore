from pydantic import BaseModel


class UserStats(BaseModel):
    integrations_number: int
    vectors_number: int
    