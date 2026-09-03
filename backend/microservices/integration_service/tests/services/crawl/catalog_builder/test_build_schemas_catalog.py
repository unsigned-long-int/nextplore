import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from sqlalchemy.engine import Engine
from sqlalchemy.engine.base import Connection

from integration_service.services.crawl.catalog_builder.build_schemas_catalog import (
    build_schemas_catalog,
)
from integration_service.services.crawl.catalogs import SchemaCatalog


class TestBuildSchemasCatalog(unittest.TestCase):
    def setUp(self):
        self.datastore_id = uuid4()

        self.mock_engine = MagicMock(spec=Engine)
        self.mock_connection = MagicMock(spec=Connection)
        self.mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=self.mock_connection
        )
        self.mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)

        self.mock_inspector = MagicMock()

        self.mock_schema_spec = MagicMock()
        self.mock_table_spec = MagicMock()

        self.mock_schemas = [
            SchemaCatalog(datastore_id=self.datastore_id, name="schema1", tables=[]),
            SchemaCatalog(datastore_id=self.datastore_id, name="schema2", tables=[]),
        ]

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_returns_schemas_from_inspect_schemas(
        self, mock_inspect, mock_inspect_schemas
    ):
        mock_inspect.return_value = self.mock_inspector
        mock_inspect_schemas.return_value = self.mock_schemas

        result = build_schemas_catalog(
            engine=self.mock_engine,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        self.assertEqual(result, self.mock_schemas)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "schema1")
        self.assertEqual(result[1].name, "schema2")

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_creates_connection_context_manager(
        self, mock_inspect, mock_inspect_schemas
    ):
        mock_inspect.return_value = self.mock_inspector
        mock_inspect_schemas.return_value = self.mock_schemas

        build_schemas_catalog(
            engine=self.mock_engine,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        self.mock_engine.connect.assert_called_once()
        self.mock_engine.connect.return_value.__enter__.assert_called_once()
        self.mock_engine.connect.return_value.__exit__.assert_called_once()

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_creates_inspector_from_connection(
        self, mock_inspect, mock_inspect_schemas
    ):
        mock_inspect.return_value = self.mock_inspector
        mock_inspect_schemas.return_value = self.mock_schemas

        build_schemas_catalog(
            engine=self.mock_engine,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        mock_inspect.assert_called_once_with(self.mock_connection)

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_calls_inspect_schemas_with_correct_parameters(
        self, mock_inspect, mock_inspect_schemas
    ):
        mock_inspect.return_value = self.mock_inspector
        mock_inspect_schemas.return_value = self.mock_schemas

        build_schemas_catalog(
            engine=self.mock_engine,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        mock_inspect_schemas.assert_called_once_with(
            crawler=self.mock_inspector,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_returns_empty_list_when_no_schemas(
        self, mock_inspect, mock_inspect_schemas
    ):
        mock_inspect.return_value = self.mock_inspector
        mock_inspect_schemas.return_value = []

        result = build_schemas_catalog(
            engine=self.mock_engine,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        self.assertEqual(result, [])
        self.assertEqual(len(result), 0)

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_connection_closed_on_success(self, mock_inspect, mock_inspect_schemas):
        mock_inspect.return_value = self.mock_inspector
        mock_inspect_schemas.return_value = self.mock_schemas

        build_schemas_catalog(
            engine=self.mock_engine,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        self.mock_engine.connect.return_value.__exit__.assert_called_once()

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_connection_closed_on_exception(self, mock_inspect, mock_inspect_schemas):
        mock_inspect.return_value = self.mock_inspector
        mock_inspect_schemas.side_effect = Exception("Inspection failed")

        with self.assertRaises(Exception) as context:
            build_schemas_catalog(
                engine=self.mock_engine,
                datastore_id=self.datastore_id,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec,
            )

        self.assertIn("Inspection failed", str(context.exception))

        self.mock_engine.connect.return_value.__exit__.assert_called_once()

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_propagates_inspect_schemas_exception(
        self, mock_inspect, mock_inspect_schemas
    ):
        mock_inspect.return_value = self.mock_inspector
        mock_inspect_schemas.side_effect = ValueError("Invalid schema specification")

        with self.assertRaises(ValueError) as context:
            build_schemas_catalog(
                engine=self.mock_engine,
                datastore_id=self.datastore_id,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec,
            )

        self.assertIn("Invalid schema specification", str(context.exception))

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_handles_connection_failure(self, mock_inspect, mock_inspect_schemas):
        self.mock_engine.connect.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception) as context:
            build_schemas_catalog(
                engine=self.mock_engine,
                datastore_id=self.datastore_id,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec,
            )

        self.assertIn("Connection failed", str(context.exception))

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_handles_inspect_failure(self, mock_inspect, mock_inspect_schemas):
        mock_inspect.side_effect = Exception("Inspector creation failed")

        with self.assertRaises(Exception) as context:
            build_schemas_catalog(
                engine=self.mock_engine,
                datastore_id=self.datastore_id,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec,
            )

        self.assertIn("Inspector creation failed", str(context.exception))

        self.mock_engine.connect.return_value.__exit__.assert_called_once()

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_works_with_different_datastore_ids(
        self, mock_inspect, mock_inspect_schemas
    ):
        datastore_id_1 = uuid4()
        datastore_id_2 = uuid4()

        mock_inspect.return_value = self.mock_inspector

        schemas_1 = [
            SchemaCatalog(datastore_id=datastore_id_1, name="schema1", tables=[])
        ]
        schemas_2 = [
            SchemaCatalog(datastore_id=datastore_id_2, name="schema2", tables=[])
        ]

        mock_inspect_schemas.side_effect = [schemas_1, schemas_2]

        result_1 = build_schemas_catalog(
            engine=self.mock_engine,
            datastore_id=datastore_id_1,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        result_2 = build_schemas_catalog(
            engine=self.mock_engine,
            datastore_id=datastore_id_2,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        self.assertEqual(result_1[0].datastore_id, datastore_id_1)
        self.assertEqual(result_2[0].datastore_id, datastore_id_2)
        self.assertEqual(mock_inspect_schemas.call_count, 2)

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_preserves_schemas_order(self, mock_inspect, mock_inspect_schemas):
        ordered_schemas = [
            SchemaCatalog(datastore_id=self.datastore_id, name="alpha", tables=[]),
            SchemaCatalog(datastore_id=self.datastore_id, name="beta", tables=[]),
            SchemaCatalog(datastore_id=self.datastore_id, name="gamma", tables=[]),
        ]

        mock_inspect.return_value = self.mock_inspector
        mock_inspect_schemas.return_value = ordered_schemas

        result = build_schemas_catalog(
            engine=self.mock_engine,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].name, "alpha")
        self.assertEqual(result[1].name, "beta")
        self.assertEqual(result[2].name, "gamma")


class TestBuildSchemasCatalogIntegration(unittest.TestCase):
    def setUp(self):
        self.datastore_id = uuid4()
        self.mock_schema_spec = MagicMock()
        self.mock_table_spec = MagicMock()

    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect_schemas"
    )
    @patch(
        "integration_service.services.crawl.catalog_builder.build_schemas_catalog.inspect"
    )
    def test_full_workflow(self, mock_inspect, mock_inspect_schemas):
        mock_engine = MagicMock(spec=Engine)
        mock_connection = MagicMock(spec=Connection)
        mock_inspector = MagicMock()

        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_inspect.return_value = mock_inspector

        expected_schemas = [
            SchemaCatalog(datastore_id=self.datastore_id, name="public", tables=[]),
            SchemaCatalog(datastore_id=self.datastore_id, name="private", tables=[]),
        ]
        mock_inspect_schemas.return_value = expected_schemas

        result = build_schemas_catalog(
            engine=mock_engine,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )

        mock_engine.connect.assert_called_once()
        mock_inspect.assert_called_once_with(mock_connection)
        mock_inspect_schemas.assert_called_once_with(
            crawler=mock_inspector,
            datastore_id=self.datastore_id,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec,
        )
        self.assertEqual(result, expected_schemas)
