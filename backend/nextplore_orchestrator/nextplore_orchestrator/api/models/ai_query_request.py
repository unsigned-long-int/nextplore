from pydantic import BaseModel


class AIQueryRequest(BaseModel):
    provider: str
    model_id: str
    prompt: str
