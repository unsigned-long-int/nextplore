import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import Mock, patch

from utils.crawlers.crawlers import crawl_tables, crawl_schemas


class TestCrawlTables(unittest.TestCase):
    def setUp(self):
        self.integration_id = uuid4()
        self.schema_name = 'public'

        self.crawler = Mock()
        self.table_spec = Mock()

    @patch('utils.crawlers.crawlers.TableCatalog')
    def test_filters_and_builds_tables(self, fake_catalog):
        self.crawler.get_table_names.return_value = ['a', 'b', 'c']
        self.table_spec.is_satisfied_by.side_effect = [True, False, True]

        self.crawler.get_columns.return_value = ['col']
        self.crawler.get_pk_constraint.return_value = {'pk': ['id']}
        self.crawler.get_foreign_keys.return_value = []
        self.crawler.get_indexes.return_value = [{'idx': 'i'}]
        self.crawler.get_table_comment.return_value = {'text': 'hello'}

        fake_catalog.side_effect=lambda **kw: SimpleNamespace(**kw)
        result = crawl_tables(self.crawler, self.integration_id, self.schema_name, self.table_spec)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        names = {t.name for t in result}
        self.assertEqual(names, {'a', 'c'})

        _, kwargs = self.crawler.get_table_names.call_args
        qschema = kwargs.get('schema')
        self.assertEqual(str(qschema), self.schema_name)
        self.assertTrue(getattr(qschema, 'quote', False))

        self.assertEqual(self.crawler.get_columns.call_count, 2)
        self.assertEqual(self.crawler.get_pk_constraint.call_count, 2)
        self.assertEqual(self.crawler.get_foreign_keys.call_count, 2)
        self.assertEqual(self.crawler.get_indexes.call_count, 2)
        self.assertEqual(self.crawler.get_table_comment.call_count, 2)

    @patch('utils.crawlers.crawlers.logger')
    @patch('utils.crawlers.crawlers.TableCatalog')
    def test_handles_per_table_exception_and_continues(self, fake_catalog, fake_logger):
        self.crawler.get_table_names.return_value = ['good', 'bad', 'another']
        self.table_spec.is_satisfied_by.return_value = True

        def columns_side_effect(*args, **kwargs):
            if kwargs.get('table_name') == 'bad':
                raise RuntimeError('boom')
            return ['cols']

        self.crawler.get_columns.side_effect = columns_side_effect
        self.crawler.get_pk_constraint.return_value = {'pk': []}
        self.crawler.get_foreign_keys.return_value = []
        self.crawler.get_indexes.return_value = []
        self.crawler.get_table_comment.return_value = {}

        fake_catalog.side_effect=lambda **kw: SimpleNamespace(**kw)
        result = crawl_tables(self.crawler, self.integration_id, self.schema_name, self.table_spec)

        names = {t.name for t in result}
        self.assertEqual(names, {'good', 'another'})

        fake_logger.error.assert_called_once()
        self.assertIn('bad', fake_logger.error.call_args.args[0])


class TestCrawlSchemas(unittest.TestCase):
    def setUp(self):
        self.integration_id = uuid4()
        self.crawler = Mock()
        self.schema_spec = Mock()
        self.table_spec = Mock()

    @patch('utils.crawlers.crawlers.crawl_tables')
    @patch('utils.crawlers.crawlers.SchemaCatalog')
    def test_filters_schemas_and_includes_only_non_empty_tables(self, mock_schema_cls, mock_crawl_tables):
        self.crawler.get_schema_names.return_value = ['public', 'internal']

        self.schema_spec.is_satisfied_by.return_value = True

        mock_schema_cls.side_effect = lambda **kw: SimpleNamespace(**kw)

        mock_crawl_tables.side_effect = [
            (SimpleNamespace(name='t1'),),
            tuple(),
        ]

        result = crawl_schemas(self.crawler, self.integration_id, self.schema_spec, self.table_spec)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, 'public')
        self.assertEqual(mock_crawl_tables.call_count, 2)

        self.assertEqual(mock_schema_cls.call_count, 3)


    @patch('utils.crawlers.crawlers.crawl_tables')
    @patch('utils.crawlers.crawlers.SchemaCatalog')
    def test_skips_unsatisfied_schemas_and_does_not_call_tables_for_them(self, mock_schema_cls, mock_crawl_tables):
        self.crawler.get_schema_names.return_value = ['public', 'internal']

        def spec_side_effect(candidate):
            return candidate.name == 'internal'

        self.schema_spec.is_satisfied_by.side_effect = spec_side_effect

        mock_schema_cls.side_effect = lambda **kw: SimpleNamespace(**kw)
        mock_crawl_tables.return_value = (SimpleNamespace(name='t2'),)

        result = crawl_schemas(self.crawler, self.integration_id, self.schema_spec, self.table_spec)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, 'internal')

        mock_crawl_tables.assert_called_once()
        args, kwargs = mock_crawl_tables.call_args
        self.assertEqual(args[1], self.integration_id)
        self.assertEqual(args[2], 'internal')
