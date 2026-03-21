import unittest
import uuid
import json
from unittest.mock import MagicMock, patch, AsyncMock
from svc_llm_inference_contracts.models import ORMContextRequest, LlmOutputSpecs, IntegrationEntry, SchemaEntry

from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse
from llm_inference_service.services.models_gateway.model_providers.openai import OpenAIProvider
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


VALID_RAW_RESPONSE = {
    'integration': INTEGRATION_ID,
    'class_name': 'Characters',
    'column_names': ['marvel.characters.power', 'marvel.characters.name'],
    'column_aggregates': [{'agg_func': 'count', 'agg_column': 'marvel.characters.power'}],
    'column_filters': [{'operator': '=', 'value': 'strong', 'filter_column': 'marvel.characters.skills'}]
}

VALID_PARSED_RESPONSE = {
    'integration': INTEGRATION_ID,
    'class_name': 'Characters',
    'schema_name': 'marvel',
    'table_name': 'characters',
    'column_names': ['power', 'name'],
    'column_aggregates': [{'agg_func': 'count', 'agg_column': 'power'}],
    'column_filters': [{'operator': '=', 'value': 'strong', 'filter_column': 'skills'}]
}


class TestOpenAIProvider(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.request = ORMContextRequest(
            provider='Deepseek',
            model_id='Deepseek-14-build',
            query='Count the powers for strong marvel characters',
            llm_output_specs=make_llm_output_specs()
        )

    def _make_completion_mock(self, function_args: dict) -> AsyncMock:
        tool_call_mock = MagicMock()
        tool_call_mock.function.arguments = json.dumps(function_args)
        choices_mock = MagicMock()
        choices_mock.message.tool_calls = [tool_call_mock]
        completion_mock = MagicMock()
        completion_mock.choices = [choices_mock]
        client = AsyncMock()
        client.chat.completions.create.return_value = completion_mock
        return client

    @patch('llm_inference_service.services.models_gateway.model_providers.openai.openai_provider.load_open_ai_client')
    async def test_successfully_retrieves_model_response(self, load_open_ai_client_mock):
        client = self._make_completion_mock(VALID_RAW_RESPONSE)
        load_open_ai_client_mock.return_value = client

        provider = OpenAIProvider(model_id='Deepseek-14-build')
        result = await provider.execute_structured_query(self.request)

        self.assertEqual(result, VALID_PARSED_RESPONSE)
        client.chat.completions.create.assert_awaited_once_with(
            model='Deepseek-14-build',
            messages=[{'role': 'user', 'content': self.request.query}],
            tools=build_tool_schema(self.request.llm_output_specs),
            tool_choice='required'
        )

    @patch('llm_inference_service.services.models_gateway.model_providers.openai.openai_provider.load_open_ai_client')
    async def test_raises_by_invalid_response_schema(self, load_open_ai_client_mock):
        client = self._make_completion_mock({'invalid_args': 'invalid'})
        load_open_ai_client_mock.return_value = client

        provider = OpenAIProvider(model_id='Deepseek-14-build')

        with self.assertRaises(InvalidModelResponse) as ctx:
            await provider.execute_structured_query(self.request)

        self.assertIn('Deepseek-14-build', str(ctx.exception))


class TestParseResponseSchema(unittest.TestCase):
    @patch('llm_inference_service.services.models_gateway.model_providers.openai.openai_provider.load_open_ai_client')
    def  setUp(self, load_open_ai_client_mock):
        client = self._make_completion_mock(VALID_RAW_RESPONSE)
        load_open_ai_client_mock.return_value = client
        self.provider = OpenAIProvider(model_id='Deepseek-14-build')


    def _make_completion_mock(self, function_args: dict) -> AsyncMock:
        tool_call_mock = MagicMock()
        tool_call_mock.function.arguments = json.dumps(function_args)
        choices_mock = MagicMock()
        choices_mock.message.tool_calls = [tool_call_mock]
        completion_mock = MagicMock()
        completion_mock.choices = [choices_mock]
        client = AsyncMock()
        client.chat.completions.create.return_value = completion_mock
        return client


    def test_strips_qualified_prefix_from_column_names(self):
        result = self.provider._parse_response_schema(VALID_RAW_RESPONSE)
        self.assertEqual(result['column_names'], ['power', 'name'])

    def test_strips_qualified_prefix_from_filter_column(self):
        result = self.provider._parse_response_schema(VALID_RAW_RESPONSE)
        self.assertEqual(result['column_filters'][0]['filter_column'], 'skills')

    def test_strips_qualified_prefix_from_agg_column(self):
        result = self.provider._parse_response_schema(VALID_RAW_RESPONSE)
        self.assertEqual(result['column_aggregates'][0]['agg_column'], 'power')

    def test_extracts_schema_name(self):
        result = self.provider._parse_response_schema(VALID_RAW_RESPONSE)
        self.assertEqual(result['schema_name'], 'marvel')

    def test_extracts_table_name(self):
        result = self.provider._parse_response_schema(VALID_RAW_RESPONSE)
        self.assertEqual(result['table_name'], 'characters')

    def test_preserves_integration_and_class_name(self):
        result = self.provider._parse_response_schema(VALID_RAW_RESPONSE)
        self.assertEqual(result['integration'], INTEGRATION_ID)
        self.assertEqual(result['class_name'], 'Characters')

    def test_preserves_filter_operator_and_value(self):
        result = self.provider._parse_response_schema(VALID_RAW_RESPONSE)
        self.assertEqual(result['column_filters'][0]['operator'], '=')
        self.assertEqual(result['column_filters'][0]['value'], 'strong')

    def test_raises_when_columns_belong_to_different_tables(self):
        mixed_response = {
            **VALID_RAW_RESPONSE,
            'column_names': ['marvel.characters.power', 'dc.heroes.name']
        }
        with self.assertRaises(InvalidModelResponse):
            self.provider._parse_response_schema(mixed_response)

    def test_empty_filters_and_aggregates(self):
        response = {
            **VALID_RAW_RESPONSE,
            'column_filters': [],
            'column_aggregates': []
        }
        result = self.provider._parse_response_schema(response)
        self.assertEqual(result['column_filters'], [])
        self.assertEqual(result['column_aggregates'], [])
