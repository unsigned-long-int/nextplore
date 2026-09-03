from pydantic import BaseModel


class UserStats(BaseModel):
    datastores_number: int
    vectors_number: int
