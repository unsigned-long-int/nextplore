import unittest
import uuid
import json
from unittest.mock import AsyncMock, MagicMock, patch
from svc_llm_inference_contracts.models import (
    ORMContextRequest,
    LlmOutputSpecs,
    IntegrationEntry,
    SchemaEntry
)

from llm_inference_service.services.models_gateway.model_providers.hugging_face.inference.inference_providers import \
    NovitaInference
from llm_inference_service.services.rag_pipeline.ai_adapter import build_tool_schema

INTEGRATION_ID = str(uuid.uuid4())


def make_llm_output_specs() -> LlmOutputSpecs:
    return LlmOutputSpecs(
        integration_registry_repr=json.dumps({
            INTEGRATION_ID: {
                'marvel': {
                    'characters': ['power', 'skills', 'age', 'height', 'weight', 'name']
                }
            }
        }),
        integrations_enum=[INTEGRATION_ID],
        schemas_enum=['marvel'],
        tables_enum=['characters'],
        columns_enum=['power', 'skills', 'age', 'height', 'weight', 'name'],
        filter_op_enum=['=', '>', '<', '!='],
        agg_funcs_enum=['avg', 'sum', 'count', 'min', 'max'],
        table_columns_registry={
            INTEGRATION_ID: IntegrationEntry(schemas={
                'marvel': SchemaEntry(tables={
                    'characters': ['power', 'skills', 'age', 'height', 'weight', 'name']
                })
            })
        }
    )


class TestNovitaInference(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.provider_name = 'novita'
        self.provider_url = 'https://huggingface.co'
        self.request = ORMContextRequest(
            provider='Deepseek',
            model_id='Deepseek-14-build',
            query='Count the powers for strong marvel characters',
            llm_output_specs=make_llm_output_specs()
        )

    @patch('llm_inference_service.services.models_gateway.model_providers.hugging_face.inference.inference_providers.novita.AsyncOpenAI')
    async def test_gets_model_response(self, openai_mock):
        func_args = {'test-arg': 'test-value'}
        tool_call_mock = MagicMock()
        tool_call_mock.function.arguments = json.dumps(func_args)
        choices_mock = MagicMock()
        choices_mock.message.tool_calls = [tool_call_mock]
        completions_request_mock = MagicMock()
        completions_request_mock.choices = [choices_mock]
        openai_instance_mock = AsyncMock()
        openai_mock.return_value = openai_instance_mock
        openai_instance_mock.chat.completions.create.return_value = completions_request_mock

        inference = NovitaInference(self.provider_name, self.provider_url)
        result = await inference.get_structured_model_response(
            'hf-path',
            300,
            orm_context_request=self.request
        )

        openai_instance_mock.chat.completions.create.assert_awaited_once_with(
            model=f'hf-path:{self.provider_name}',
            messages=[{'role': 'user', 'content': self.request.query}],
            tools=build_tool_schema(self.request.llm_output_specs),
            tool_choice='required',
            max_tokens=300
        )
        self.assertEqual(result, func_args)

