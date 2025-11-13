from typing import Dict, Any
from abc import ABC, abstractmethod

from ai_orm_context_service.api.models.orm_context_request import ORMContextRequest


class InferenceProviderBase(ABC):
    def __init__(self, provider_name: str, provider_url: str) -> None:
        self.provider_name = provider_name
        self.provider_url = provider_url

    @abstractmethod
    async def get_model_response(
        self,
        hf_path: str,
        max_tokens: int,
        orm_context_request: ORMContextRequest
    ) -> Dict[str, Any]:
        pass

    def __repr__(self) -> str:
        return f'Provider: {self.provider_name}, URL: {self.provider_url}'
