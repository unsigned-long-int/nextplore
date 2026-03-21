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
        parsed = self._parse_response_schema(response)
        if not self._validate_response_schema(parsed):
            msg = f'Invalid structured query model response. Model: {self.model.model_id}. Provider: {self.inference_provider!r}. Response: {parsed}'
            raise InvalidModelResponse(msg)
        return parsed

    async def execute_query(self, query: str) -> str:
        response = await self.inference_provider.get_model_response(
            hf_path=self.model.hf_path,
            max_tokens=self.model.max_tokens,
            query=query
        )
        if len(response.strip().splitlines()) < 2:
            raise InvalidModelResponse(f'Invalid chat model response. Model: {self.model.model_id}. Provider: {self.inference_provider!r}')
        return response

    @staticmethod
    def _validate_response_schema(model_response: Dict[str, Any]) -> bool:
        try:
            ORMContextResponse(**model_response)
            return True
        except ValidationError:
            return False

    def _parse_response_schema(self, model_response: Dict[str, Any]) -> Dict[str, Any]:
        if 'column_names' not in model_response or not model_response['column_names']:
            msg = f'Missing or empty column_names in response. Model: {self.model.model_id}. Provider: {self.inference_provider!r}. Response: {model_response}'
            raise InvalidModelResponse(msg)
        first_col = model_response['column_names'][0]
        parts = first_col.split('.')
        schema_name, table_name = parts[0], parts[1]

        for col in model_response['column_names']:
            if not col.startswith(f'{schema_name}.{table_name}.'):
                msg = f'Parsing failed. Column {col} does not belong to {schema_name}.{table_name}. Model: {self.model.model_id}. Provider: {self.inference_provider!r}, Response: {model_response}'
                raise InvalidModelResponse(msg)

        return {
            'integration': model_response['integration'],
            'class_name': model_response['class_name'],
            'schema_name': schema_name,
            'table_name': table_name,
            'column_names': [c.split('.')[2] for c in model_response['column_names']],
            'column_filters': [
                {**f, 'filter_column': f['filter_column'].split('.')[2]}
                for f in model_response['column_filters']
            ],
            'column_aggregates': [
                {**a, 'agg_column': a['agg_column'].split('.')[2]}
                for a in model_response['column_aggregates']
            ]
        }