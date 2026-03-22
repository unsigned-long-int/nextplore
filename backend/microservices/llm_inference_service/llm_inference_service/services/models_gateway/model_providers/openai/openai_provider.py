import os
import json
from typing import Dict, List, Any
from pydantic import ValidationError
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionToolParam

from llm_inference_service.services.rag_pipeline.ai_adapter import build_tool_schema
from llm_inference_service.services.models_gateway.model_providers.base import BaseProvider
from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse

from svc_llm_inference_contracts.models import ORMContextResponse, ORMContextRequest
from nextplore_sdk.open_ai_client_loader.open_ai_client_loader import load_open_ai_client

class OpenAIProvider(BaseProvider):
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        self.client = load_open_ai_client(os.getenv('OPENAI_API_KEY'))

    async def execute_structured_query(self, orm_context_request: ORMContextRequest) -> Dict[str, Any]:
        llm_output_specs = orm_context_request.llm_output_specs
        tools: List[ChatCompletionToolParam] = build_tool_schema(llm_output_specs)
        messages: List[ChatCompletionUserMessageParam] = [
            {'role': 'user', 'content': orm_context_request.query}
        ]

        request = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            tools=tools,
            tool_choice='required'
        )
        tool_call = request.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        parsed = self._parse_response_schema(args)
        if not self._validate_response_schema(parsed):
            msg = f'Invalid structured model response. Model: {self.model_id}. Provider: OpenAI. Response: {parsed}'
            raise InvalidModelResponse(msg)
        return parsed

    async def execute_query(self, query: str) -> str:
        response = await self.client.responses.create(
            model=self.model_id,
            input=query,
        )
        if len(response.output_text.strip().splitlines()) < 2:
            msg = f'Invalid chat model response. Model: {self.model_id}. Provider: OpenAI. Response: {response}'
            raise InvalidModelResponse(msg)
        return response.output_text

    async def prompt_model(self, prompt: str) -> str:
        response = await self.client.responses.create(
            model=self.model_id,
            input=prompt,
        )
        return response.output_text

    @staticmethod
    def _validate_response_schema(model_response: Dict[str, Any]) -> bool:
        try:
            ORMContextResponse(**model_response)
            return True
        except ValidationError:
            return False

    def _parse_response_schema(self, model_response: Dict[str, Any]) -> Dict[str, Any]:
        if 'column_names' not in model_response or not model_response['column_names']:
            msg = f'Missing or empty column_names in response. Model: {self.model_id}. Provider: OpenAI. Response: {model_response}'
            raise InvalidModelResponse(msg)
        first_col = model_response['column_names'][0]
        parts = first_col.split('.')
        schema_name, table_name = parts[0], parts[1]

        for col in model_response['column_names']:
            if not col.startswith(f'{schema_name}.{table_name}.'):
                msg = f'Parsing failed. Column {col} does not belong to {schema_name}.{table_name}. Model: OpenAI. Provider: OpenAI, Response: {model_response}'
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