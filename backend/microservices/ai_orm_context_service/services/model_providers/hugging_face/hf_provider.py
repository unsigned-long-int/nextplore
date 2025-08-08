from typing import Dict, Any
from pydantic import ValidationError

from nextplore_shared.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest
from nextplore_shared.contracts.ai_orm_context_service.orm_context_response import ORMContextResponse
from services.model_providers.hugging_face.inference.inference_providers import InferenceProviderBase
from services.exceptions import InvalidModelResponse
from services.model_providers.hugging_face.hf_model import HFModel
from services.model_providers.base import BaseProvider


class HFProvider(BaseProvider):
    def __init__(self, model: HFModel, inference_provider: InferenceProviderBase) -> None:
        self.model = model
        self.inference_provider = inference_provider

    async def retrieve_model_response(self, orm_context_request: ORMContextRequest) -> Dict[str, Any]:
        response = await self.inference_provider.get_model_response(
            hf_path=self.model.hf_path, 
            max_tokens=self.model.max_tokens, 
            orm_context_request=orm_context_request
        )
        if not self._validate_response_schema(response):
            msg = f'Invalid model response. Model: {self.model.model_id}. Provider: {self.inference_provider!r}'
            raise InvalidModelResponse(msg)
        return response
    
    def _validate_response_schema(self, model_response: Dict[str, Any]) -> bool:
        try:
            ORMContextResponse(**model_response)
            return True
        except ValidationError:
            return False
