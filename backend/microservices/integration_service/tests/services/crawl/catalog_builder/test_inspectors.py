import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from sqlalchemy import quoted_name
from sqlalchemy.engine.reflection import Inspector

from integration_service.services.crawl.catalog_builder.inspectors import (
    inspect_tables,
    inspect_schemas
)
from integration_service.services.crawl.catalogs import (
    SchemaCatalog,
    TableCatalog
)


class TestInspectTables(unittest.TestCase):

    def setUp(self):
        self.integration_id = uuid4()
        self.schema_name = 'test_schema'

        self.mock_inspector = MagicMock(spec=Inspector)

        self.mock_table_spec = MagicMock()
        self.mock_table_spec.is_satisfied_by = MagicMock(return_value=True)

        self.mock_columns = [
            {'name': 'id', 'type': 'INTEGER'},
            {'name': 'name', 'type': 'VARCHAR'}
        ]
        self.mock_pk_constraint = {'constrained_columns': ['id']}
        self.mock_foreign_keys = []
        self.mock_indexes = [{'name': 'idx_name', 'column_names': ['name']}]
        self.mock_table_comment = {'text': 'Test table'}

    def test_returns_empty_tuple_when_no_tables(self):
        self.mock_inspector.get_table_names.return_value = []

        result = inspect_tables(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_name=self.schema_name,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(result, ())
        self.assertEqual(len(result), 0)
        self.mock_inspector.get_table_names.assert_called_once()

    def test_gets_table_names_with_quoted_schema(self):
        self.mock_inspector.get_table_names.return_value = []

        inspect_tables(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_name=self.schema_name,
            table_spec=self.mock_table_spec
        )

        call_args = self.mock_inspector.get_table_names.call_args
        schema_arg = call_args[1]['schema']

        self.assertIsInstance(schema_arg, quoted_name)
        self.assertEqual(str(schema_arg), self.schema_name)

    def test_returns_tables_satisfying_spec(self):
        self.mock_inspector.get_table_names.return_value = ['table1', 'table2']
        self.mock_inspector.get_columns.return_value = self.mock_columns
        self.mock_inspector.get_pk_constraint.return_value = self.mock_pk_constraint
        self.mock_inspector.get_foreign_keys.return_value = self.mock_foreign_keys
        self.mock_inspector.get_indexes.return_value = self.mock_indexes
        self.mock_inspector.get_table_comment.return_value = self.mock_table_comment

        result = inspect_tables(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_name=self.schema_name,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0].name, 'table1')
        self.assertEqual(result[1].name, 'table2')

    def test_skips_tables_not_satisfying_spec(self):
        self.mock_inspector.get_table_names.return_value = ['table1', 'table2', 'table3']

        def is_satisfied_side_effect(candidate):
            return candidate.name in ['table1', 'table3']

        self.mock_table_spec.is_satisfied_by.side_effect = is_satisfied_side_effect

        self.mock_inspector.get_columns.return_value = self.mock_columns
        self.mock_inspector.get_pk_constraint.return_value = self.mock_pk_constraint
        self.mock_inspector.get_foreign_keys.return_value = self.mock_foreign_keys
        self.mock_inspector.get_indexes.return_value = self.mock_indexes
        self.mock_inspector.get_table_comment.return_value = self.mock_table_comment

        result = inspect_tables(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_name=self.schema_name,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, 'table1')
        self.assertEqual(result[1].name, 'table3')

    def test_includes_all_table_metadata(self):
        self.mock_inspector.get_table_names.return_value = ['users']
        self.mock_inspector.get_columns.return_value = self.mock_columns
        self.mock_inspector.get_pk_constraint.return_value = self.mock_pk_constraint
        self.mock_inspector.get_foreign_keys.return_value = self.mock_foreign_keys
        self.mock_inspector.get_indexes.return_value = self.mock_indexes
        self.mock_inspector.get_table_comment.return_value = self.mock_table_comment

        result = inspect_tables(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_name=self.schema_name,
            table_spec=self.mock_table_spec
        )

        table = result[0]
        self.assertIsInstance(table, TableCatalog)
        self.assertEqual(table.integration_id, self.integration_id)
        self.assertEqual(table.name, 'users')
        self.assertEqual(table.columns, self.mock_columns)
        self.assertEqual(table.primary_keys, self.mock_pk_constraint)
        self.assertEqual(table.foreign_keys, self.mock_foreign_keys)
        self.assertEqual(table.indexes, self.mock_indexes)
        self.assertEqual(table.table_comment, self.mock_table_comment)

    def test_calls_inspector_methods_with_correct_parameters(self):
        table_name = 'test_table'
        self.mock_inspector.get_table_names.return_value = [table_name]
        self.mock_inspector.get_columns.return_value = self.mock_columns
        self.mock_inspector.get_pk_constraint.return_value = self.mock_pk_constraint
        self.mock_inspector.get_foreign_keys.return_value = self.mock_foreign_keys
        self.mock_inspector.get_indexes.return_value = self.mock_indexes
        self.mock_inspector.get_table_comment.return_value = self.mock_table_comment

        inspect_tables(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_name=self.schema_name,
            table_spec=self.mock_table_spec
        )

        self.mock_inspector.get_columns.assert_called_once_with(
            table_name=table_name,
            schema=self.schema_name
        )
        self.mock_inspector.get_pk_constraint.assert_called_once_with(
            table_name=table_name,
            schema=self.schema_name
        )
        self.mock_inspector.get_foreign_keys.assert_called_once_with(
            table_name=table_name,
            schema=self.schema_name
        )
        self.mock_inspector.get_indexes.assert_called_once_with(
            table_name=table_name,
            schema=self.schema_name
        )
        self.mock_inspector.get_table_comment.assert_called_once_with(
            table_name=table_name,
            schema=self.schema_name
        )

    @patch('integration_service.services.crawl.catalog_builder.inspectors.logger')
    def test_handles_exception_during_inspection(self, mock_logger):
        self.mock_inspector.get_table_names.return_value = ['table1', 'table2']

        def get_columns_side_effect(*args, **kwargs):
            if kwargs.get('table_name') == 'table1':
                raise Exception('Column inspection failed')
            return self.mock_columns

        self.mock_inspector.get_columns.side_effect = get_columns_side_effect
        self.mock_inspector.get_pk_constraint.return_value = self.mock_pk_constraint
        self.mock_inspector.get_foreign_keys.return_value = self.mock_foreign_keys
        self.mock_inspector.get_indexes.return_value = self.mock_indexes
        self.mock_inspector.get_table_comment.return_value = self.mock_table_comment

        result = inspect_tables(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_name=self.schema_name,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, 'table2')

        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args[0][0]
        self.assertIn('Failed to inspect table', error_message)
        self.assertIn('table1', error_message)

    @patch('integration_service.services.crawl.catalog_builder.inspectors.logger')
    def test_continues_after_exception(self, mock_logger):
        self.mock_inspector.get_table_names.return_value = ['table1', 'table2', 'table3']

        call_count = [0]

        def get_columns_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception('Inspection failed')
            return self.mock_columns

        self.mock_inspector.get_columns.side_effect = get_columns_side_effect
        self.mock_inspector.get_pk_constraint.return_value = self.mock_pk_constraint
        self.mock_inspector.get_foreign_keys.return_value = self.mock_foreign_keys
        self.mock_inspector.get_indexes.return_value = self.mock_indexes
        self.mock_inspector.get_table_comment.return_value = self.mock_table_comment

        result = inspect_tables(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_name=self.schema_name,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, 'table1')
        self.assertEqual(result[1].name, 'table3')

    def test_returns_tuple_type(self):
        self.mock_inspector.get_table_names.return_value = ['table1']
        self.mock_inspector.get_columns.return_value = self.mock_columns
        self.mock_inspector.get_pk_constraint.return_value = self.mock_pk_constraint
        self.mock_inspector.get_foreign_keys.return_value = self.mock_foreign_keys
        self.mock_inspector.get_indexes.return_value = self.mock_indexes
        self.mock_inspector.get_table_comment.return_value = self.mock_table_comment

        result = inspect_tables(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_name=self.schema_name,
            table_spec=self.mock_table_spec
        )

        self.assertIsInstance(result, tuple)
        self.assertNotIsInstance(result, list)


class TestInspectSchemas(unittest.TestCase):

    def setUp(self):
        self.integration_id = uuid4()

        self.mock_inspector = MagicMock(spec=Inspector)

        self.mock_schema_spec = MagicMock()
        self.mock_schema_spec.is_satisfied_by = MagicMock(return_value=True)

        self.mock_table_spec = MagicMock()
        self.mock_table_spec.is_satisfied_by = MagicMock(return_value=True)

        self.mock_tables = (
            TableCatalog(integration_id=self.integration_id, name='table1'),
            TableCatalog(integration_id=self.integration_id, name='table2')
        )

    def test_returns_empty_tuple_when_no_schemas(self):
        self.mock_inspector.get_schema_names.return_value = []

        result = inspect_schemas(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(result, ())
        self.assertEqual(len(result), 0)

    @patch('integration_service.services.crawl.catalog_builder.inspectors.inspect_tables')
    def test_returns_schemas_with_tables(self, mock_inspect_tables):
        self.mock_inspector.get_schema_names.return_value = ['schema1', 'schema2']
        mock_inspect_tables.return_value = self.mock_tables

        result = inspect_schemas(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0].name, 'schema1')
        self.assertEqual(result[1].name, 'schema2')
        self.assertEqual(result[0].tables, self.mock_tables)
        self.assertEqual(result[1].tables, self.mock_tables)

    @patch('integration_service.services.crawl.catalog_builder.inspectors.inspect_tables')
    def test_skips_schemas_not_satisfying_spec(self, mock_inspect_tables):
        self.mock_inspector.get_schema_names.return_value = ['schema1', 'schema2', 'schema3']

        def is_satisfied_side_effect(candidate):
            return candidate.name in ['schema1', 'schema3']

        self.mock_schema_spec.is_satisfied_by.side_effect = is_satisfied_side_effect
        mock_inspect_tables.return_value = self.mock_tables

        result = inspect_schemas(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, 'schema1')
        self.assertEqual(result[1].name, 'schema3')

        self.assertEqual(mock_inspect_tables.call_count, 2)

    @patch('integration_service.services.crawl.catalog_builder.inspectors.inspect_tables')
    def test_skips_schemas_with_no_tables(self, mock_inspect_tables):
        self.mock_inspector.get_schema_names.return_value = ['schema1', 'schema2', 'schema3']

        def inspect_tables_side_effect(crawler, integration_id, schema_name, table_spec):
            if schema_name == 'schema2':
                return ()
            return self.mock_tables

        mock_inspect_tables.side_effect = inspect_tables_side_effect

        result = inspect_schemas(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, 'schema1')
        self.assertEqual(result[1].name, 'schema3')

    @patch('integration_service.services.crawl.catalog_builder.inspectors.inspect_tables')
    def test_calls_inspect_tables_with_correct_parameters(self, mock_inspect_tables):
        schema_name = 'test_schema'
        self.mock_inspector.get_schema_names.return_value = [schema_name]
        mock_inspect_tables.return_value = self.mock_tables

        inspect_schemas(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        mock_inspect_tables.assert_called_once_with(
            self.mock_inspector,
            self.integration_id,
            schema_name,
            self.mock_table_spec
        )

    @patch('integration_service.services.crawl.catalog_builder.inspectors.inspect_tables')
    def test_creates_schema_catalog_with_correct_attributes(self, mock_inspect_tables):
        schema_name = 'public'
        self.mock_inspector.get_schema_names.return_value = [schema_name]
        mock_inspect_tables.return_value = self.mock_tables

        result = inspect_schemas(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        schema = result[0]
        self.assertIsInstance(schema, SchemaCatalog)
        self.assertEqual(schema.integration_id, self.integration_id)
        self.assertEqual(schema.name, schema_name)
        self.assertEqual(schema.tables, self.mock_tables)

    @patch('integration_service.services.crawl.catalog_builder.inspectors.inspect_tables')
    def test_returns_tuple_type(self, mock_inspect_tables):
        self.mock_inspector.get_schema_names.return_value = ['schema1']
        mock_inspect_tables.return_value = self.mock_tables

        result = inspect_schemas(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertIsInstance(result, tuple)
        self.assertNotIsInstance(result, list)

    @patch('integration_service.services.crawl.catalog_builder.inspectors.inspect_tables')
    def test_handles_multiple_schemas_with_different_table_counts(self, mock_inspect_tables):
        self.mock_inspector.get_schema_names.return_value = ['schema1', 'schema2', 'schema3']

        tables_1 = (TableCatalog(integration_id=self.integration_id, name='t1'),)
        tables_2 = (
            TableCatalog(integration_id=self.integration_id, name='t2'),
            TableCatalog(integration_id=self.integration_id, name='t3'),
            TableCatalog(integration_id=self.integration_id, name='t4'),
        )
        tables_3 = ()

        mock_inspect_tables.side_effect = [tables_1, tables_2, tables_3]

        result = inspect_schemas(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0].tables), 1)
        self.assertEqual(len(result[1].tables), 3)

    @patch('integration_service.services.crawl.catalog_builder.inspectors.inspect_tables')
    def test_preserves_schema_order(self, mock_inspect_tables):
        self.mock_inspector.get_schema_names.return_value = ['alpha', 'beta', 'gamma']
        mock_inspect_tables.return_value = self.mock_tables

        result = inspect_schemas(
            crawler=self.mock_inspector,
            integration_id=self.integration_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(result[0].name, 'alpha')
        self.assertEqual(result[1].name, 'beta')
        self.assertEqual(result[2].name, 'gamma')


class TestInspectorsIntegration(unittest.TestCase):

    @patch('integration_service.services.crawl.catalog_builder.inspectors.inspect_tables')
    def test_full_workflow(self, mock_inspect_tables):
        integration_id = uuid4()
        mock_inspector = MagicMock(spec=Inspector)
        mock_schema_spec = MagicMock()
        mock_table_spec = MagicMock()

        mock_schema_spec.is_satisfied_by = MagicMock(return_value=True)

        mock_inspector.get_schema_names.return_value = ['public', 'private']

        public_tables = (
            TableCatalog(integration_id=integration_id, name='users'),
            TableCatalog(integration_id=integration_id, name='posts'),
        )
        private_tables = (
            TableCatalog(integration_id=integration_id, name='credentials'),
        )

        mock_inspect_tables.side_effect = [public_tables, private_tables]

        result = inspect_schemas(
            crawler=mock_inspector,
            integration_id=integration_id,
            schema_spec=mock_schema_spec,
            table_spec=mock_table_spec
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, 'public')
        self.assertEqual(len(result[0].tables), 2)
        self.assertEqual(result[1].name, 'private')
        self.assertEqual(len(result[1].tables), 1)

        self.assertEqual(mock_inspect_tables.call_count, 2)
        mock_inspect_tables.assert_any_call(
            mock_inspector, integration_id, 'public', mock_table_spec
        )
        mock_inspect_tables.assert_any_call(
            mock_inspector, integration_id, 'private', mock_table_spec
        )
