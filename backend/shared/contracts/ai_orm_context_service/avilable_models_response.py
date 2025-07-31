from pydantic import BaseModel
from typing import List


class ModelInfo(BaseModel):
    model_id: str
    label: str
    tags: List[str]


class AvailableModelsResponse(BaseModel):
    models: List[ModelInfo]
