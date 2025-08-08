import unittest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from services.model_providers.hugging_face.hf_provider import HFProvider
from services.exceptions import InvalidModelResponse
from nextplore_shared.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest, Context


class TestHFProvider(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_model = MagicMock()
        self.mock_model.hf_path = 'test/hf-path'
        self.mock_model.max_tokens = 512
        self.mock_model.model_id = 'test-model'

        self.mock_inference_provider = AsyncMock()

        self.provider = HFProvider(
            model=self.mock_model,
            inference_provider=self.mock_inference_provider
        )

        self.valid_response: Dict[str, Any] = {
            'integration': 'my_integration',
            'schema_name': 'schema',
            'class_name': 'MyClass',
            'table_name': 'my_table',
            'column_names': ['col1', 'col2'],
            'column_aggregates': [{'sum': 'col1'}],
            'column_filters': [{'operator': '=', 'value': 42, 'filter_column': 'col2'}]
        }

        self.invalid_response: Dict[str, Any] = {
            'bad_field': 'unexpected'
        }

        self.request = ORMContextRequest(
            provider='huggingface',
            model_id='test-model',
            query='Show me data',
            context=Context(
                integration_registry_repr='repr',
                integrations_enum=['int1'],
                schemas_enum=['schema'],
                tables_enum=['table'],
                columns_enum=['col1', 'col2'],
                filter_op_enum=['='],
                agg_funcs_enum=['sum']
            )
        )

    async def test_retrieve_model_response_valid(self):
        self.mock_inference_provider.get_model_response.return_value = self.valid_response

        result = await self.provider.retrieve_model_response(self.request)

        self.assertEqual(result, self.valid_response)
        self.mock_inference_provider.get_model_response.assert_awaited_once()

    async def test_retrieve_model_response_invalid_raises(self):
        self.mock_inference_provider.get_model_response.return_value = self.invalid_response

        with self.assertRaises(InvalidModelResponse) as ctx:
            await self.provider.retrieve_model_response(self.request)

        self.assertIn('Invalid model response', str(ctx.exception))
        self.mock_inference_provider.get_model_response.assert_awaited_once()

    def test_validate_response_schema_valid(self):
        is_valid = self.provider._validate_response_schema(self.valid_response)
        self.assertTrue(is_valid)

    def test_validate_response_schema_invalid(self):
        is_valid = self.provider._validate_response_schema(self.invalid_response)
        self.assertFalse(is_valid)
