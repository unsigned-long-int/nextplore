import unittest
import uuid
from unittest.mock import MagicMock, AsyncMock
from svc_llm_inference_contracts.models import ORMContextRequest, LlmOutputSpecs

from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse
from llm_inference_service.services.models_gateway.model_providers.hugging_face import HFProvider


class TestHFProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.model = MagicMock()
        self.inference_provider = MagicMock()
        self.inference_provider.get_structured_model_response = AsyncMock()
        self.request = ORMContextRequest(
            provider='Deepseek',
            model_id='Deepseek-14-build',
            query='Count the powers for strong marvel characters',
            llm_output_specs=LlmOutputSpecs(
                integration_registry_repr='general',
                integrations_enum=[str(uuid.uuid4()), str(uuid.uuid4())],
                schemas_enum=['marvel', 'dc', 'startrek'],
                tables_enum=['characters', 'relatives', 'realms'],
                columns_enum=['power', 'skills', 'age', 'height', 'weight', 'skills', 'name'],
                filter_op_enum=['=', '>', '<', '!='],
                agg_funcs_enum=['avg', 'sum', 'count', 'min', 'max']
            )
        )

    async def test_successfully_retrieves_model_response(self):
        hf_path = 'test-path'
        max_tokens = 300
        valid_response = {
            'integration': uuid.uuid4(),
            'schema_name': 'schema',
            'class_name': 'MyClass',
            'table_name': 'my_table',
            'column_names': ['col1', 'col2'],
            'column_aggregates': [{'sum': 'col1'}],
            'column_filters': [{'operator': '=', 'value': 42, 'filter_column': 'col2'}]
        }

        self.model.hf_path = hf_path
        self.model.max_tokens = max_tokens
        self.inference_provider.get_structured_model_response.return_value = valid_response
        provider = HFProvider(
            model=self.model,
            inference_provider = self.inference_provider
        )
        result = await provider.execute_structured_query(self.request)
        self.assertEqual(result, valid_response)
        self.inference_provider.get_structured_model_response.assert_awaited_once_with(
            hf_path=hf_path,
            max_tokens=max_tokens,
            orm_context_request=self.request
        )

    async def test_raises_by_invalid_response(self):
        hf_path = 'test-path'
        max_tokens = 300
        invalid_response = {
            'invalid_response': 'invalid'
        }

        self.model.hf_path = hf_path
        self.model.model_id = 'failed_id'
        self.model.max_tokens = max_tokens
        self.inference_provider.get_structured_model_response.return_value = invalid_response
        provider = HFProvider(
            model=self.model,
            inference_provider=self.inference_provider
        )
        with self.assertRaises(InvalidModelResponse) as ctx:
            await provider.execute_structured_query(self.request)
        self.assertIn('failed_id', str(ctx.exception))