import unittest
import uuid
import json
from unittest.mock import MagicMock, AsyncMock
from svc_llm_inference_contracts.models import ORMContextRequest, LlmOutputSpecs, IntegrationEntry, SchemaEntry

from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse
from llm_inference_service.services.models_gateway.model_providers.hugging_face import HFProvider


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


class TestHFProvider(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.model = MagicMock()
        self.model.hf_path = 'test-path'
        self.model.max_tokens = 300
        self.model.model_id = 'Deepseek-14-build'
        self.inference_provider = MagicMock()
        self.inference_provider.get_structured_model_response = AsyncMock()
        self.request = ORMContextRequest(
            provider='Deepseek',
            model_id='Deepseek-14-build',
            query='Count the powers for strong marvel characters',
            llm_output_specs=make_llm_output_specs()
        )

    async def test_successfully_retrieves_model_response(self):
        self.inference_provider.get_structured_model_response.return_value = VALID_RAW_RESPONSE

        provider = HFProvider(
            model=self.model,
            inference_provider=self.inference_provider
        )
        result = await provider.execute_structured_query(self.request)

        self.assertEqual(result, VALID_PARSED_RESPONSE)
        self.inference_provider.get_structured_model_response.assert_awaited_once_with(
            hf_path='test-path',
            max_tokens=300,
            orm_context_request=self.request
        )

    async def test_raises_by_invalid_response(self):
        self.model.model_id = 'failed_id'
        self.inference_provider.get_structured_model_response.return_value = {'invalid_response': 'invalid'}

        provider = HFProvider(
            model=self.model,
            inference_provider=self.inference_provider
        )
        with self.assertRaises(InvalidModelResponse) as ctx:
            await provider.execute_structured_query(self.request)

        self.assertIn('failed_id', str(ctx.exception))

    async def test_raises_when_columns_belong_to_different_tables(self):
        mixed_response = {
            **VALID_RAW_RESPONSE,
            'column_names': ['marvel.characters.power', 'dc.heroes.name']
        }
        self.inference_provider.get_structured_model_response.return_value = mixed_response

        provider = HFProvider(model=self.model, inference_provider=self.inference_provider)
        with self.assertRaises(InvalidModelResponse):
            await provider.execute_structured_query(self.request)

    async def test_raises_when_column_names_empty(self):
        empty_response = {
            **VALID_RAW_RESPONSE,
            'column_names': []
        }
        self.inference_provider.get_structured_model_response.return_value = empty_response

        provider = HFProvider(model=self.model, inference_provider=self.inference_provider)
        with self.assertRaises(InvalidModelResponse):
            await provider.execute_structured_query(self.request)
