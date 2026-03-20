from typing import Dict, Any
from pydantic import ValidationError
from svc_llm_inference_contracts.models import ORMContextRequest, ORMContextResponse

from llm_inference_service.services.models_gateway.model_providers.hugging_face.inference.inference_providers import InferenceProviderBase
from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse
from llm_inference_service.domain.models.hf_model import HFModel
from llm_inference_service.services.models_gateway.model_providers.base import BaseProvider


class HFProvider(BaseProvider):
    def __init__(self, model: HFModel, inference_provider: InferenceProviderBase) -> None:
        self.model = model
        self.inference_provider = inference_provider

    async def execute_structured_query(self, orm_context_request: ORMContextRequest) -> Dict[str, Any]:
        response = await self.inference_provider.get_structured_model_response(
            hf_path=self.model.hf_path, 
            max_tokens=self.model.max_tokens, 
            orm_context_request=orm_context_request
        )
        if not self._validate_response_schema(response):
            msg = f'Invalid model response. Model: {self.model.model_id}. Provider: {self.inference_provider!r}'
            raise InvalidModelResponse(msg)
        return response

    async def execute_query(self, query: str) -> str:
        response = await self.inference_provider.get_model_response(
            hf_path=self.model.hf_path,
            max_tokens=self.model.max_tokens,
            query=query
        )
        if len(response.strip().splitlines()) < 2:
            raise InvalidModelResponse(f'Invalid model response. Model: {self.model.model_id}. Provider: {self.inference_provider!r}')
        return response
    
    def _validate_response_schema(self, model_response: Dict[str, Any]) -> bool:
        try:
            ORMContextResponse(**model_response)
            return True
        except ValidationError:
            return False
