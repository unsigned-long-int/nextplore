import unittest
import uuid

from ai_orm_context_service.domain.models.orm_context import ORMContext
from ai_orm_context_service.services.orm_context.ai_adapter import adapt_llm_response


class TestAdaptLLMResponse(unittest.TestCase):
    def test_adapt_llm_response(self):
        integration = uuid.uuid4()
        response = {
            'integration': integration,
            'schema_name': 'marvel',
            'class_name': 'marvel_characters',
            'table_name': 'characters',
            'column_names': ['age', 'power', 'skills'],
            'column_aggregates': [{'count': 'power'}],
            'column_filters': [{'operator': '=', 'value': 'strong', 'filter_column': 'skills'}]
        }
        result = adapt_llm_response(response)
        self.assertIsInstance(result, ORMContext)
        self.assertEqual(result.integration, integration)
        self.assertEqual(result.schema_name, 'marvel')
