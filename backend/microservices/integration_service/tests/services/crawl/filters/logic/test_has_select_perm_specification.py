import unittest
from unittest.mock import MagicMock, patch

from integration_service.services.crawl.filters.logic import HasSelectPermissionSpec
from integration_service.services.crawl.catalogs import TableCatalog
from uuid import uuid4


class TestHasSelectPermissionSpec(unittest.TestCase):

    def setUp(self):
        self.integration_id = uuid4()
        self.schema_name = 'test_schema'
        self.mock_crawler = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_crawler.bind.connect.return_value.__enter__ = MagicMock(return_value=self.mock_conn)
        self.mock_crawler.bind.connect.return_value.__exit__ = MagicMock(return_value=False)

    def _make_candidate(self, name: str):
        return TableCatalog(integration_id=self.integration_id, name=name)

    def _make_result(self, table_names):
        return [(name,) for name in table_names]

    def test_is_satisfied_by_returns_true_when_accessible_is_none(self):
        self.mock_crawler.dialect.name = 'oracle'
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertIsNone(spec._accessible)
        self.assertTrue(spec.is_satisfied_by(self._make_candidate('any_table')))

    def test_is_satisfied_by_returns_true_for_accessible_table(self):
        self.mock_crawler.dialect.name = 'mssql'
        self.mock_conn.execute.return_value = self._make_result(['table1', 'table2'])
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertTrue(spec.is_satisfied_by(self._make_candidate('table1')))

    def test_is_satisfied_by_returns_false_for_inaccessible_table(self):
        self.mock_crawler.dialect.name = 'mssql'
        self.mock_conn.execute.return_value = self._make_result(['table1'])
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertFalse(spec.is_satisfied_by(self._make_candidate('restricted_table')))

    def test_mssql_fetches_accessible_tables(self):
        self.mock_crawler.dialect.name = 'mssql'
        self.mock_conn.execute.return_value = self._make_result(['table1', 'table2', 'table3'])
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertEqual(spec._accessible, {'table1', 'table2', 'table3'})

    def test_mssql_returns_empty_set_when_no_tables_accessible(self):
        self.mock_crawler.dialect.name = 'mssql'
        self.mock_conn.execute.return_value = self._make_result([])
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertEqual(spec._accessible, set())

    def test_mssql_executes_with_correct_schema_param(self):
        self.mock_crawler.dialect.name = 'mssql'
        self.mock_conn.execute.return_value = self._make_result([])
        HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        call_args = self.mock_conn.execute.call_args
        self.assertEqual(call_args[0][1], {'schema': self.schema_name})

    def test_postgresql_fetches_accessible_tables(self):
        self.mock_crawler.dialect.name = 'postgresql'
        self.mock_conn.execute.return_value = self._make_result(['users', 'orders'])
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertEqual(spec._accessible, {'users', 'orders'})

    def test_postgresql_executes_with_correct_schema_param(self):
        self.mock_crawler.dialect.name = 'postgresql'
        self.mock_conn.execute.return_value = self._make_result([])
        HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        call_args = self.mock_conn.execute.call_args
        self.assertEqual(call_args[0][1], {'schema': self.schema_name})

    def test_mysql_fetches_accessible_tables(self):
        self.mock_crawler.dialect.name = 'mysql'
        self.mock_conn.execute.return_value = self._make_result(['products', 'customers'])
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertEqual(spec._accessible, {'products', 'customers'})

    def test_mysql_executes_with_correct_schema_param(self):
        self.mock_crawler.dialect.name = 'mysql'
        self.mock_conn.execute.return_value = self._make_result([])
        HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        call_args = self.mock_conn.execute.call_args
        self.assertEqual(call_args[0][1], {'schema': self.schema_name})

    def test_unsupported_dialect_returns_none(self):
        self.mock_crawler.dialect.name = 'oracle'
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertIsNone(spec._accessible)

    def test_unsupported_dialect_satisfies_all_candidates(self):
        self.mock_crawler.dialect.name = 'oracle'
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertTrue(spec.is_satisfied_by(self._make_candidate('any_table')))
        self.assertTrue(spec.is_satisfied_by(self._make_candidate('another_table')))

    @patch('integration_service.services.crawl.filters.logic.has_select_perm_specification.logger')
    def test_returns_none_on_exception(self, mock_logger):
        self.mock_crawler.dialect.name = 'mssql'
        self.mock_conn.execute.side_effect = Exception('DB connection error')
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertIsNone(spec._accessible)

    @patch('integration_service.services.crawl.filters.logic.has_select_perm_specification.logger')
    def test_logs_warning_on_exception(self, mock_logger):
        self.mock_crawler.dialect.name = 'mssql'
        self.mock_conn.execute.side_effect = Exception('DB connection error')
        HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        mock_logger.warning.assert_called_once()
        self.assertIn(self.schema_name, mock_logger.warning.call_args[0][0])

    @patch('integration_service.services.crawl.filters.logic.has_select_perm_specification.logger')
    def test_satisfies_all_on_exception(self, mock_logger):
        self.mock_crawler.dialect.name = 'mssql'
        self.mock_conn.execute.side_effect = Exception('DB connection error')
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertTrue(spec.is_satisfied_by(self._make_candidate('any_table')))

    def test_snowflake_probes_each_table(self):
        self.mock_crawler.dialect.name = 'snowflake'
        self.mock_crawler.get_table_names.return_value = ['table1', 'table2', 'table3']
        self.mock_conn.execute.return_value = MagicMock()
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertEqual(spec._accessible, {'table1', 'table2', 'table3'})
        self.assertEqual(self.mock_conn.execute.call_count, 3)

    def test_snowflake_excludes_inaccessible_tables(self):
        self.mock_crawler.dialect.name = 'snowflake'
        self.mock_crawler.get_table_names.return_value = ['table1', 'table2', 'table3']

        def execute_side_effect(stmt):
            if 'table2' in stmt.text:
                raise Exception('Permission denied')
            return MagicMock()

        self.mock_conn.execute.side_effect = execute_side_effect
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertEqual(spec._accessible, {'table1', 'table3'})

    def test_snowflake_returns_empty_set_when_no_access(self):
        self.mock_crawler.dialect.name = 'snowflake'
        self.mock_crawler.get_table_names.return_value = ['table1', 'table2']
        self.mock_conn.execute.side_effect = Exception('Permission denied')
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertEqual(spec._accessible, set())

    @patch('integration_service.services.crawl.filters.logic.has_select_perm_specification.logger')
    def test_snowflake_handles_table_listing_failure(self, mock_logger):
        self.mock_crawler.dialect.name = 'snowflake'
        self.mock_crawler.get_table_names.side_effect = Exception('Listing failed')
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertEqual(spec._accessible, set())
        mock_logger.warning.assert_called_once()
        self.assertIn('Snowflake table listing failed', mock_logger.warning.call_args[0][0])

    def test_snowflake_probes_with_correct_sql(self):
        self.mock_crawler.dialect.name = 'snowflake'
        self.mock_crawler.get_table_names.return_value = ['my_table']
        self.mock_conn.execute.return_value = MagicMock()
        HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        executed_sql = self.mock_conn.execute.call_args[0][0].text
        self.assertIn(self.schema_name, executed_sql)
        self.assertIn('my_table', executed_sql)
        self.assertIn('SELECT 1', executed_sql)

    def test_snowflake_returns_empty_set_when_no_tables(self):
        self.mock_crawler.dialect.name = 'snowflake'
        self.mock_crawler.get_table_names.return_value = []
        spec = HasSelectPermissionSpec(self.mock_crawler, self.schema_name)
        self.assertEqual(spec._accessible, set())
        self.mock_conn.execute.assert_not_called()