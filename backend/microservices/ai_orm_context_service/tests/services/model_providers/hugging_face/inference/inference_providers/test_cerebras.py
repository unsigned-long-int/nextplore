import unittest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from services.model_providers.hugging_face.inference.inference_providers.cerebras import CerebrasInference
from nextplore_sdk.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest, Context

@patch('services.model_providers.hugging_face.inference.inference_providers.cerebras.AsyncOpenAI')
class TestCerebrasInference(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.provider_name = 'cerebras'
        self.provider_url = 'https://fake.cerebras.api'

        self.request = ORMContextRequest(
            provider='huggingface',
            model_id='fake-model',
            query='Give me sales summary',
            context=Context(
                integration_registry_repr='some_repr',
                integrations_enum=['int1'],
                schemas_enum=['schema1'],
                tables_enum=['table1'],
                columns_enum=['col1', 'col2'],
                filter_op_enum=['='],
                agg_funcs_enum=['sum']
            )
        )

        self.expected_args = {
            'integration': 'int1',
            'schema_name': 'schema1',
            'class_name': 'Sales',
            'table_name': 'table1',
            'column_names': ['col1', 'col2'],
            'column_filters': [{'operator': '=', 'value': 100, 'filter_column': 'col2'}],
            'column_aggregates': [{'agg_func': 'sum', 'agg_column': 'col1'}]
        }

    async def test_get_model_response(self, mock_openai_client):
        mock_tool_call = MagicMock()
        mock_tool_call.function.arguments = json.dumps(self.expected_args)

        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client_instance = AsyncMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance

        inference = CerebrasInference(self.provider_name, self.provider_url)

        result = await inference.get_model_response(
            hf_path='hf/test-model',
            max_tokens=500,
            orm_context_request=self.request
        )

        self.assertEqual(result, self.expected_args)

        mock_client_instance.chat.completions.create.assert_awaited_once_with(
            model='hf/test-model:cerebras',
            messages=[{'role': 'user', 'content': 'Give me sales summary'}],
            tools=inference._build_function_schema(self.request.context),
            tool_choice='required',
            max_tokens=500
        )

    def test_build_function_schema_structure(self, _):
        inference = CerebrasInference(self.provider_name, self.provider_url)
        tools = inference._build_function_schema(self.request.context)

        self.assertIsInstance(tools, list)
        self.assertEqual(tools[0]['type'], 'function')
        func = tools[0]['function']
        self.assertEqual(func['name'], 'generate_orm_class')
        self.assertIn('integration', func['parameters']['properties'])
        self.assertEqual(
            func['parameters']['properties']['integration']['enum'],
            self.request.context.integrations_enum
        )
        self.assertIn('column_aggregates', func['parameters']['properties'])
        self.assertEqual(func['parameters']['required'], [
            'integration', 'schema_name', 'class_name', 'table_name', 'column_names',
            'column_filters', 'column_aggregates'
        ])
