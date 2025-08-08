import unittest
from services.orm_context_builder.ai_adapter import adapt_llm_response
from services.orm_context_builder.orm_context_model import ORMContext


class TestAdaptLLMResponse(unittest.TestCase):

    def setUp(self):
        self.valid_response = {
            'integration': 'salesforce',
            'schema_name': 'public',
            'class_name': 'Customer',
            'table_name': 'customers',
            'column_names': ['id', 'name', 'email'],
            'column_filters': [{'column': 'country', 'operator': '=', 'value': 'USA'}],
            'column_aggregates': [{'function': 'count', 'column': 'id'}]
        }

    def test_valid_response(self):
        context = adapt_llm_response(self.valid_response)

        self.assertIsInstance(context, ORMContext)
        self.assertEqual(context.integration, 'salesforce')
        self.assertEqual(context.schema_name, 'public')
        self.assertEqual(context.class_name, 'Customer')
        self.assertEqual(context.table_name, 'customers')
        self.assertEqual(context.column_names, ['id', 'name', 'email'])
        self.assertEqual(context.column_filters[0]['column'], 'country')
        self.assertEqual(context.column_aggregates[0]['function'], 'count')

    def test_missing_key_raises_key_error(self):
        for key in self.valid_response:
            with self.subTest(f'missing key: {key}'):
                invalid = self.valid_response.copy()
                invalid.pop(key)
                with self.assertRaises(KeyError):
                    adapt_llm_response(invalid)
