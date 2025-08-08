import unittest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from services.model_providers.openai.openai_provider import OpenAIProvider
from services.exceptions import InvalidModelResponse
from nextplore_shared.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest, Context


class TestOpenAIProvider(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.model_id = 'gpt-4'
        self.valid_args = {
            'integration': 'int1',
            'schema_name': 'schema1',
            'class_name': 'Sales',
            'table_name': 'table1',
            'column_names': ['col1', 'col2'],
            'column_filters': [{'operator': '=', 'value': 100, 'filter_column': 'col2'}],
            'column_aggregates': [{'agg_func': 'sum', 'agg_column': 'col1'}]
        }

        self.context = Context(
            integration_registry_repr='repr',
            integrations_enum=['int1'],
            schemas_enum=['schema1'],
            tables_enum=['table1'],
            columns_enum=['col1', 'col2'],
            filter_op_enum=['='],
            agg_funcs_enum=['sum']
        )

        self.request = ORMContextRequest(
            provider='openai',
            model_id=self.model_id,
            query='Show me the sales summary',
            context=self.context
        )

    @patch('services.model_providers.openai.openai_provider.load_open_ai_client')
    async def test_retrieve_model_response_valid(self, mock_load_client):
        mock_tool_call = MagicMock()
        mock_tool_call.function.arguments = json.dumps(self.valid_args)

        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_load_client.return_value = mock_client

        provider = OpenAIProvider(model_id=self.model_id)

        result = await provider.retrieve_model_response(self.request)

        self.assertEqual(result, self.valid_args)
        mock_client.chat.completions.create.assert_awaited_once_with(
            model=self.model_id,
            messages=[{'role': 'user', 'content': self.request.query}],
            tools=provider._build_function_schema(self.context),
            tool_choice='required'
        )

    @patch('services.model_providers.openai.openai_provider.load_open_ai_client')
    async def test_retrieve_model_response_invalid_raises(self, mock_load_client):
        invalid_args = {'unexpected': 'value'}
        mock_tool_call = MagicMock()
        mock_tool_call.function.arguments = json.dumps(invalid_args)

        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_load_client.return_value = mock_client

        provider = OpenAIProvider(model_id=self.model_id)

        with self.assertRaises(InvalidModelResponse):
            await provider.retrieve_model_response(self.request)

    @patch('services.model_providers.openai.openai_provider.load_open_ai_client')
    def test_validate_response_schema(self, _):
        provider = OpenAIProvider(model_id=self.model_id)

        self.assertTrue(provider._validate_response_schema(self.valid_args))

        self.assertFalse(provider._validate_response_schema({'unexpected': 'bad'}))

    @patch('services.model_providers.openai.openai_provider.load_open_ai_client')
    def test_build_function_schema_structure(self, _):
        provider = OpenAIProvider(model_id=self.model_id)
        tools = provider._build_function_schema(self.context)

        self.assertIsInstance(tools, list)
        self.assertEqual(tools[0]['type'], 'function')

        func = tools[0]['function']
        self.assertEqual(func['name'], 'generate_orm_class')
        self.assertIn('integration', func['parameters']['properties'])
        self.assertIn('column_aggregates', func['parameters']['properties'])
        self.assertEqual(func['parameters']['required'], [
            'integration', 'schema_name', 'class_name', 'table_name',
            'column_names', 'column_filters', 'column_aggregates'
        ])
