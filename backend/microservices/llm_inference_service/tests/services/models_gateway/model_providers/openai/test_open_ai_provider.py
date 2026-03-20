import unittest
import uuid
import json
from unittest.mock import MagicMock, patch, AsyncMock
from svc_llm_inference_contracts.models import ORMContextRequest, Context

from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse
from llm_inference_service.services.models_gateway.model_providers import OpenAIProvider


class TestOpenAIProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.request = ORMContextRequest(
            provider='Deepseek',
            model_id='Deepseek-14-build',
            query='Count the powers for strong marvel characters',
            context=Context(
                integration_registry_repr='general',
                integrations_enum=[str(uuid.uuid4()), str(uuid.uuid4())],
                schemas_enum=['marvel', 'dc', 'startrek'],
                tables_enum=['characters', 'relatives', 'realms'],
                columns_enum=['power', 'skills', 'age', 'height', 'weight', 'skills', 'name'],
                filter_op_enum=['=', '>', '<', '!='],
                agg_funcs_enum=['avg', 'sum', 'count', 'min', 'max']
            )
        )

    @patch('llm_inference_service.services.orm_context.model_providers.openai.openai_provider.load_open_ai_client')
    async def test_successfully_retrieves_model_response(
        self,
        load_open_ai_client_mock
    ):
        client = AsyncMock()
        valid_function_args = {
            'integration': str(uuid.uuid4()),
            'schema_name': 'schema',
            'class_name': 'MyClass',
            'table_name': 'my_table',
            'column_names': ['col1', 'col2'],
            'column_aggregates': [{'sum': 'col1'}],
            'column_filters': [{'operator': '=', 'value': 42, 'filter_column': 'col2'}]
        }
        tool_call_mock = MagicMock()
        tool_call_mock.function.arguments = json.dumps(valid_function_args)
        choices_mock = MagicMock()
        choices_mock.message.tool_calls = [tool_call_mock]
        completions_request_mock = MagicMock()
        completions_request_mock.choices = [choices_mock]
        client.chat.completions.create.return_value = completions_request_mock
        load_open_ai_client_mock.return_value = client

        provider = OpenAIProvider(
            model_id='Deepseek-14-build'
        )
        result = await provider.execute_structured_query(self.request)
        self.assertEqual(result, valid_function_args)
        client.chat.completions.create.assert_awaited_once_with(
            model='Deepseek-14-build',
            messages=[{'role': 'user', 'content': self.request.query}],
            tools=provider._build_function_schema(self.request.context),
            tool_choice='required'
        )

    @patch('llm_inference_service.services.orm_context.model_providers.openai.openai_provider.load_open_ai_client')
    async def test_raises_by_invalid_response_schema(
        self,
        load_open_ai_client_mock
    ):
        client = AsyncMock()
        invalid_function_args = {
            'invalid_args': 'invalid'
        }
        tool_call_mock = MagicMock()
        tool_call_mock.function.arguments = json.dumps(invalid_function_args)
        choices_mock = MagicMock()
        choices_mock.message.tool_calls = [tool_call_mock]
        completions_request_mock = MagicMock()
        completions_request_mock.choices = [choices_mock]
        client.chat.completions.create.return_value = completions_request_mock
        load_open_ai_client_mock.return_value = client

        provider = OpenAIProvider(
            model_id='Deepseek-14-build'
        )
        with self.assertRaises(InvalidModelResponse) as ctx:
            await provider.execute_structured_query(self.request)

        self.assertIn('Deepseek-14-build', str(ctx.exception))
