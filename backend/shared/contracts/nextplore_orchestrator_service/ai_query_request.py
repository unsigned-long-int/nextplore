from pydantic import BaseModel


class AIQueryRequest(BaseModel):
    model_id: str
    prompt: str
