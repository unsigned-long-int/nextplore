import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import patch

from utils.filters.factory.specs_factory import create_specs


class TestCreateSpecs(unittest.TestCase):
    @patch('utils.filters.factory.specs_factory.TableNameSpec')
    @patch('utils.filters.factory.specs_factory.SchemaNameSpec')
    @patch('utils.filters.factory.specs_factory.IntegrationIdSpec')
    def test_builds_specs_with_sets_and_preserves_uuid_keys(
        self, mock_integration_spec, mock_schema_spec, mock_table_spec
    ):
        mock_integration_spec.side_effect = lambda **kw: SimpleNamespace(**kw)
        mock_schema_spec.side_effect = lambda **kw: SimpleNamespace(**kw)
        mock_table_spec.side_effect = lambda **kw: SimpleNamespace(**kw)

        u1, u2 = uuid4(), uuid4()

        integrations = [u1, u1, u2]
        schemas = {
            u1: ['public', 'public', 'sales'],
            u2: ['internal'],
        }
        tables = {
            u1: ['t1', 't1', 't2'],
            u2: [], 
        }

        integration_spec, schema_spec, table_spec = create_specs(integrations, schemas, tables)

        self.assertEqual(integration_spec.integration_ids, {u1, u2})

        self.assertEqual(
            schema_spec.allowed_integration_schemas,
            {u1: {'public', 'sales'}, u2: {'internal'}},
        )
        self.assertEqual(
            table_spec.allowed_integration_tables,
            {u1: {'t1', 't2'}, u2: set()},
        )

        mock_integration_spec.assert_called_once()
        mock_schema_spec.assert_called_once()
        mock_table_spec.assert_called_once()

    @patch('utils.filters.factory.specs_factory.TableNameSpec')
    @patch('utils.filters.factory.specs_factory.SchemaNameSpec')
    @patch('utils.filters.factory.specs_factory.IntegrationIdSpec')
    def test_empty_inputs(self, mock_integration_spec, mock_schema_spec, mock_table_spec):
        mock_integration_spec.side_effect = lambda **kw: SimpleNamespace(**kw)
        mock_schema_spec.side_effect = lambda **kw: SimpleNamespace(**kw)
        mock_table_spec.side_effect = lambda **kw: SimpleNamespace(**kw)

        integration_spec, schema_spec, table_spec = create_specs([], {}, {})

        self.assertEqual(integration_spec.integration_ids, set())
        self.assertEqual(schema_spec.allowed_integration_schemas, {})
        self.assertEqual(table_spec.allowed_integration_tables, {})
