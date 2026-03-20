from typing import Dict, Any
from abc import ABC, abstractmethod
from svc_llm_inference_contracts.models import ORMContextRequest


class InferenceProviderBase(ABC):
    def __init__(self, provider_name: str, provider_url: str) -> None:
        self.provider_name = provider_name
        self.provider_url = provider_url

    @abstractmethod
    async def get_structured_model_response(
        self,
        hf_path: str,
        max_tokens: int,
        orm_context_request: ORMContextRequest
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def get_model_response(
        self,
        hf_path: str,
        max_tokens: int,
        query: str
    ) -> str:
        ...

    def __repr__(self) -> str:
        return f'Provider: {self.provider_name}, URL: {self.provider_url}'
