import unittest
from uuid import uuid4
from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse
from llm_inference_service.services.rag_pipeline.ai_adapter import parse_response_schema

DATASTORE_ID = uuid4()


def make_valid_response(**overrides) -> dict:
    defaults = {
        'datastore': DATASTORE_ID,
        'class_name': 'SalesRecord',
        'column_names': ['public.sales.region', 'public.sales.amount'],
        'column_filters': [],
        'column_aggregates': [],
    }
    return {**defaults, **overrides}


class TestParseResponseSchema(unittest.TestCase):

    def _parse(self, response=None, **overrides):
        return parse_response_schema(
            response or make_valid_response(**overrides),
            model_id='gpt-4o',
            provider_name='OpenAI'
        )


    def test_returns_parsed_dict(self):
        result = self._parse()
        self.assertIsInstance(result, dict)

    def test_extracts_schema_and_table_from_first_column(self):
        result = self._parse()
        self.assertEqual(result['schema_name'], 'public')
        self.assertEqual(result['table_name'], 'sales')

    def test_strips_schema_table_prefix_from_column_names(self):
        result = self._parse()
        self.assertEqual(result['column_names'], ['region', 'amount'])

    def test_preserves_datastore_and_class_name(self):
        result = self._parse()
        self.assertEqual(result['datastore'], DATASTORE_ID)
        self.assertEqual(result['class_name'], 'SalesRecord')

    def test_strips_prefix_from_filter_column(self):
        response = make_valid_response(column_filters=[
            {'filter_column': 'public.sales.region', 'op': 'eq', 'value': 'EMEA'}
        ])
        result = self._parse(response)
        self.assertEqual(result['column_filters'][0]['filter_column'], 'region')

    def test_preserves_filter_fields_except_column(self):
        response = make_valid_response(column_filters=[
            {'filter_column': 'public.sales.region', 'op': 'eq', 'value': 'EMEA'}
        ])
        result = self._parse(response)
        self.assertEqual(result['column_filters'][0]['op'], 'eq')
        self.assertEqual(result['column_filters'][0]['value'], 'EMEA')

    def test_strips_prefix_from_aggregate_column(self):
        response = make_valid_response(column_aggregates=[
            {'agg_column': 'public.sales.amount', 'agg_func': 'sum'}
        ])
        result = self._parse(response)
        self.assertEqual(result['column_aggregates'][0]['agg_column'], 'amount')

    def test_preserves_aggregate_fields_except_column(self):
        response = make_valid_response(column_aggregates=[
            {'agg_column': 'public.sales.amount', 'agg_func': 'sum'}
        ])
        result = self._parse(response)
        self.assertEqual(result['column_aggregates'][0]['agg_func'], 'sum')

    def test_handles_empty_filters_and_aggregates(self):
        result = self._parse()
        self.assertEqual(result['column_filters'], [])
        self.assertEqual(result['column_aggregates'], [])

    def test_handles_multiple_filters(self):
        response = make_valid_response(column_filters=[
            {'filter_column': 'public.sales.region', 'op': 'eq', 'value': 'EMEA'},
            {'filter_column': 'public.sales.amount', 'op': 'gt', 'value': 100},
        ])
        result = self._parse(response)
        self.assertEqual(result['column_filters'][0]['filter_column'], 'region')
        self.assertEqual(result['column_filters'][1]['filter_column'], 'amount')


    def test_raises_when_column_names_missing(self):
        response = make_valid_response()
        del response['column_names']
        with self.assertRaises(InvalidModelResponse):
            self._parse(response)

    def test_raises_when_column_names_empty(self):
        with self.assertRaises(InvalidModelResponse):
            self._parse(column_names=[])

    def test_error_message_contains_model_id_when_column_names_missing(self):
        with self.assertRaises(InvalidModelResponse) as ctx:
            self._parse(column_names=[])
        self.assertIn('gpt-4o', str(ctx.exception))


    def test_raises_when_columns_span_multiple_tables(self):
        with self.assertRaises(InvalidModelResponse):
            self._parse(column_names=[
                'public.sales.region',
                'public.orders.amount',
            ])

    def test_raises_when_columns_span_multiple_schemas(self):
        with self.assertRaises(InvalidModelResponse):
            self._parse(column_names=[
                'public.sales.region',
                'analytics.sales.region',
            ])

    def test_error_message_contains_offending_column(self):
        with self.assertRaises(InvalidModelResponse) as ctx:
            self._parse(column_names=[
                'public.sales.region',
                'public.orders.amount',
            ])
        self.assertIn('public.orders.amount', str(ctx.exception))


    def test_raises_when_orm_context_response_validation_fails(self):
        with self.assertRaises(InvalidModelResponse):
            self._parse(make_valid_response(datastore=None))

    def test_validation_error_message_contains_model_and_provider(self):
        with self.assertRaises(InvalidModelResponse) as ctx:
            self._parse(make_valid_response(datastore=None))
        self.assertIn('gpt-4o', str(ctx.exception))
        self.assertIn('OpenAI', str(ctx.exception))