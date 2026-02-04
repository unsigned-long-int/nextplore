import unittest
from uuid import UUID, uuid4
from integration_service.services.crawl.filters.specs import (
    IntegrationIdSpec,
    SchemaNameSpec,
    TableNameSpec
)
from integration_service.services.crawl.filters.factory import create_specs


class TestCreateSpecs(unittest.TestCase):
    def test_create_specs_with_single_integration(self):
        integration_id = uuid4()
        integrations = [integration_id]
        schemas = {str(integration_id): ['public', 'analytics']}
        tables = {str(integration_id): ['users', 'orders']}

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        self.assertIsInstance(integration_spec, IntegrationIdSpec)
        self.assertIsInstance(schema_spec, SchemaNameSpec)
        self.assertIsInstance(table_spec, TableNameSpec)

        self.assertEqual(integration_spec.allowed, {integration_id})
        self.assertEqual(
            schema_spec.allowed,
            {integration_id: {'public', 'analytics'}}
        )
        self.assertEqual(
            table_spec.allowed,
            {integration_id: {'users', 'orders'}}
        )

    def test_create_specs_with_multiple_integrations(self):
        integration_id_1 = uuid4()
        integration_id_2 = uuid4()
        integrations = [integration_id_1, integration_id_2]
        schemas = {
            str(integration_id_1): ['public', 'analytics'],
            str(integration_id_2): ['staging', 'production']
        }
        tables = {
            str(integration_id_1): ['users', 'orders'],
            str(integration_id_2): ['products', 'inventory']
        }

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        self.assertEqual(
            integration_spec.allowed,
            {integration_id_1, integration_id_2}
        )
        self.assertEqual(
            schema_spec.allowed,
            {
                integration_id_1: {'public', 'analytics'},
                integration_id_2: {'staging', 'production'}
            }
        )
        self.assertEqual(
            table_spec.allowed,
            {
                integration_id_1: {'users', 'orders'},
                integration_id_2: {'products', 'inventory'}
            }
        )

    def test_create_specs_with_empty_lists(self):
        integrations = []
        schemas = {}
        tables = {}

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        self.assertEqual(integration_spec.allowed, set())
        self.assertEqual(schema_spec.allowed, {})
        self.assertEqual(table_spec.allowed, {})

    def test_create_specs_with_empty_schema_and_table_lists(self):
        integration_id = uuid4()
        integrations = [integration_id]
        schemas = {str(integration_id): []}
        tables = {str(integration_id): []}

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        self.assertEqual(integration_spec.allowed, {integration_id})
        self.assertEqual(
            schema_spec.allowed,
            {integration_id: set()}
        )
        self.assertEqual(
            table_spec.allowed,
            {integration_id: set()}
        )

    def test_create_specs_converts_string_keys_to_uuids(self):
        integration_id = uuid4()
        integration_id_str = str(integration_id)
        integrations = [integration_id]
        schemas = {integration_id_str: ['public']}
        tables = {integration_id_str: ['users']}

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        for key in schema_spec.allowed.keys():
            self.assertIsInstance(key, UUID)
        for key in table_spec.allowed.keys():
            self.assertIsInstance(key, UUID)

    def test_create_specs_deduplicates_integration_ids(self):
        integration_id = uuid4()
        integrations = [integration_id, integration_id, integration_id]
        schemas = {str(integration_id): ['public']}
        tables = {str(integration_id): ['users']}

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        self.assertEqual(len(integration_spec.allowed), 1)
        self.assertEqual(integration_spec.allowed, {integration_id})

    def test_create_specs_with_special_characters_in_names(self):
        integration_id = uuid4()
        integrations = [integration_id]
        schemas = {
            str(integration_id): ['public-schema', 'test.schema', 'my_schema']
        }
        tables = {
            str(integration_id): ['user-data', 'order.details', 'product_info']
        }

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        self.assertEqual(
            schema_spec.allowed,
            {integration_id: {'public-schema', 'test.schema', 'my_schema'}}
        )
        self.assertEqual(
            table_spec.allowed,
            {integration_id: {'user-data', 'order.details', 'product_info'}}
        )

    def test_create_specs_with_mismatched_integration_counts(self):
        integration_id_1 = uuid4()
        integration_id_2 = uuid4()
        integration_id_3 = uuid4()

        integrations = [integration_id_1, integration_id_2, integration_id_3]
        schemas = {str(integration_id_1): ['public']}
        tables = {str(integration_id_1): ['users']}

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        self.assertEqual(
            integration_spec.allowed,
            {integration_id_1, integration_id_2, integration_id_3}
        )
        self.assertEqual(len(schema_spec.allowed), 1)
        self.assertEqual(len(table_spec.allowed), 1)

    def test_create_specs_returns_tuple_of_three_elements(self):
        integration_id = uuid4()
        integrations = [integration_id]
        schemas = {str(integration_id): ['public']}
        tables = {str(integration_id): ['users']}

        result = create_specs(integrations, schemas, tables)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_create_specs_with_one_integration(self):
        self._test_with_n_integrations(1)

    def test_create_specs_with_three_integrations(self):
        self._test_with_n_integrations(3)

    def test_create_specs_with_five_integrations(self):
        self._test_with_n_integrations(5)

    def test_create_specs_with_ten_integrations(self):
        self._test_with_n_integrations(10)

    def _test_with_n_integrations(self, integration_count):
        integration_ids = [uuid4() for _ in range(integration_count)]
        schemas = {
            str(iid): [f'schema_{i}']
            for i, iid in enumerate(integration_ids)
        }
        tables = {
            str(iid): [f'table_{i}']
            for i, iid in enumerate(integration_ids)
        }

        integration_spec, schema_spec, table_spec = create_specs(
            integration_ids, schemas, tables
        )

        self.assertEqual(len(integration_spec.allowed), integration_count)
        self.assertEqual(
            len(schema_spec.allowed),
            integration_count
        )
        self.assertEqual(
            len(table_spec.allowed),
            integration_count
        )

    def test_create_specs_preserves_schema_values_as_sets(self):
        integration_id = uuid4()
        integrations = [integration_id]
        schemas = {str(integration_id): ['public', 'analytics', 'public']}
        tables = {str(integration_id): ['users']}

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        schema_set = schema_spec.allowed[integration_id]
        self.assertIsInstance(schema_set, set)
        self.assertEqual(schema_set, {'public', 'analytics'})
        self.assertEqual(len(schema_set), 2)

    def test_create_specs_preserves_table_values_as_sets(self):
        integration_id = uuid4()
        integrations = [integration_id]
        schemas = {str(integration_id): ['public']}
        tables = {str(integration_id): ['users', 'orders', 'users']}

        integration_spec, schema_spec, table_spec = create_specs(
            integrations, schemas, tables
        )

        table_set = table_spec.allowed[integration_id]
        self.assertIsInstance(table_set, set)
        self.assertEqual(table_set, {'users', 'orders'})
        self.assertEqual(len(table_set), 2)
