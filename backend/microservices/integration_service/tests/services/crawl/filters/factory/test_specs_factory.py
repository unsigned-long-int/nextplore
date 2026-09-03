import unittest
from uuid import UUID, uuid4

from integration_service.services.crawl.filters.factory import create_specs
from integration_service.services.crawl.filters.specs import (
    DataStoreIdSpec,
    SchemaNameSpec,
    TableNameSpec,
)


class TestCreateSpecs(unittest.TestCase):
    def test_create_specs_with_single_datastore(self):
        datastore_id = uuid4()
        datastores = [datastore_id]
        schemas = {str(datastore_id): ["public", "analytics"]}
        tables = {str(datastore_id): ["users", "orders"]}

        datastore_spec, schema_spec, table_spec = create_specs(
            datastores, schemas, tables
        )

        self.assertIsInstance(datastore_spec, DataStoreIdSpec)
        self.assertIsInstance(schema_spec, SchemaNameSpec)
        self.assertIsInstance(table_spec, TableNameSpec)

        self.assertEqual(datastore_spec.allowed, {datastore_id})
        self.assertEqual(schema_spec.allowed, {datastore_id: {"public", "analytics"}})
        self.assertEqual(table_spec.allowed, {datastore_id: {"users", "orders"}})

    def test_create_specs_with_multiple_datastores(self):
        datastore_id_1 = uuid4()
        datastore_id_2 = uuid4()
        datastores = [datastore_id_1, datastore_id_2]
        schemas = {
            str(datastore_id_1): ["public", "analytics"],
            str(datastore_id_2): ["staging", "production"],
        }
        tables = {
            str(datastore_id_1): ["users", "orders"],
            str(datastore_id_2): ["products", "inventory"],
        }

        datastore_spec, schema_spec, table_spec = create_specs(
            datastores, schemas, tables
        )

        self.assertEqual(datastore_spec.allowed, {datastore_id_1, datastore_id_2})
        self.assertEqual(
            schema_spec.allowed,
            {
                datastore_id_1: {"public", "analytics"},
                datastore_id_2: {"staging", "production"},
            },
        )
        self.assertEqual(
            table_spec.allowed,
            {
                datastore_id_1: {"users", "orders"},
                datastore_id_2: {"products", "inventory"},
            },
        )

    def test_create_specs_with_empty_lists(self):
        datastores = []
        schemas = {}
        tables = {}

        datastore_spec, schema_spec, table_spec = create_specs(
            datastores, schemas, tables
        )

        self.assertEqual(datastore_spec.allowed, set())
        self.assertEqual(schema_spec.allowed, {})
        self.assertEqual(table_spec.allowed, {})

    def test_create_specs_with_empty_schema_and_table_lists(self):
        datastore_id = uuid4()
        datastores = [datastore_id]
        schemas = {str(datastore_id): []}
        tables = {str(datastore_id): []}

        datastore_spec, schema_spec, table_spec = create_specs(
            datastores, schemas, tables
        )

        self.assertEqual(datastore_spec.allowed, {datastore_id})
        self.assertEqual(schema_spec.allowed, {datastore_id: set()})
        self.assertEqual(table_spec.allowed, {datastore_id: set()})

    def test_create_specs_converts_string_keys_to_uuids(self):
        datastore_id = uuid4()
        datastore_id_str = str(datastore_id)
        datastores = [datastore_id]
        schemas = {datastore_id_str: ["public"]}
        tables = {datastore_id_str: ["users"]}

        _datastore_spec, schema_spec, table_spec = create_specs(
            datastores, schemas, tables
        )

        for key in schema_spec.allowed:
            self.assertIsInstance(key, UUID)
        for key in table_spec.allowed:
            self.assertIsInstance(key, UUID)

    def test_create_specs_deduplicates_datastore_ids(self):
        datastore_id = uuid4()
        datastores = [datastore_id, datastore_id, datastore_id]
        schemas = {str(datastore_id): ["public"]}
        tables = {str(datastore_id): ["users"]}

        datastore_spec, _schema_spec, _table_spec = create_specs(
            datastores, schemas, tables
        )

        self.assertEqual(len(datastore_spec.allowed), 1)
        self.assertEqual(datastore_spec.allowed, {datastore_id})

    def test_create_specs_with_special_characters_in_names(self):
        datastore_id = uuid4()
        datastores = [datastore_id]
        schemas = {str(datastore_id): ["public-schema", "test.schema", "my_schema"]}
        tables = {str(datastore_id): ["user-data", "order.details", "product_info"]}

        _datastore_spec, schema_spec, table_spec = create_specs(
            datastores, schemas, tables
        )

        self.assertEqual(
            schema_spec.allowed,
            {datastore_id: {"public-schema", "test.schema", "my_schema"}},
        )
        self.assertEqual(
            table_spec.allowed,
            {datastore_id: {"user-data", "order.details", "product_info"}},
        )

    def test_create_specs_with_mismatched_datastore_counts(self):
        datastore_id_1 = uuid4()
        datastore_id_2 = uuid4()
        datastore_id_3 = uuid4()

        datastores = [datastore_id_1, datastore_id_2, datastore_id_3]
        schemas = {str(datastore_id_1): ["public"]}
        tables = {str(datastore_id_1): ["users"]}

        datastore_spec, schema_spec, table_spec = create_specs(
            datastores, schemas, tables
        )

        self.assertEqual(
            datastore_spec.allowed, {datastore_id_1, datastore_id_2, datastore_id_3}
        )
        self.assertEqual(len(schema_spec.allowed), 1)
        self.assertEqual(len(table_spec.allowed), 1)

    def test_create_specs_returns_tuple_of_three_elements(self):
        datastore_id = uuid4()
        datastores = [datastore_id]
        schemas = {str(datastore_id): ["public"]}
        tables = {str(datastore_id): ["users"]}

        result = create_specs(datastores, schemas, tables)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_create_specs_with_one_datastore(self):
        self._test_with_n_datastores(1)

    def test_create_specs_with_three_datastores(self):
        self._test_with_n_datastores(3)

    def test_create_specs_with_five_datastores(self):
        self._test_with_n_datastores(5)

    def test_create_specs_with_ten_datastores(self):
        self._test_with_n_datastores(10)

    def _test_with_n_datastores(self, datastore_count):
        datastore_ids = [uuid4() for _ in range(datastore_count)]
        schemas = {str(iid): [f"schema_{i}"] for i, iid in enumerate(datastore_ids)}
        tables = {str(iid): [f"table_{i}"] for i, iid in enumerate(datastore_ids)}

        datastore_spec, schema_spec, table_spec = create_specs(
            datastore_ids, schemas, tables
        )

        self.assertEqual(len(datastore_spec.allowed), datastore_count)
        self.assertEqual(len(schema_spec.allowed), datastore_count)
        self.assertEqual(len(table_spec.allowed), datastore_count)

    def test_create_specs_preserves_schema_values_as_sets(self):
        datastore_id = uuid4()
        datastores = [datastore_id]
        schemas = {str(datastore_id): ["public", "analytics", "public"]}
        tables = {str(datastore_id): ["users"]}

        _datastore_spec, schema_spec, _table_spec = create_specs(
            datastores, schemas, tables
        )

        schema_set = schema_spec.allowed[datastore_id]
        self.assertIsInstance(schema_set, set)
        self.assertEqual(schema_set, {"public", "analytics"})
        self.assertEqual(len(schema_set), 2)

    def test_create_specs_preserves_table_values_as_sets(self):
        datastore_id = uuid4()
        datastores = [datastore_id]
        schemas = {str(datastore_id): ["public"]}
        tables = {str(datastore_id): ["users", "orders", "users"]}

        _datastore_spec, _schema_spec, table_spec = create_specs(
            datastores, schemas, tables
        )

        table_set = table_spec.allowed[datastore_id]
        self.assertIsInstance(table_set, set)
        self.assertEqual(table_set, {"users", "orders"})
        self.assertEqual(len(table_set), 2)
