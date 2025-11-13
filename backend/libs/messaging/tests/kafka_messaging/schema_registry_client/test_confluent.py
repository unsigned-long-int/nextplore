import unittest
from unittest.mock import patch, MagicMock

from kafka_messaging.schema_registry_client.confluent import ConfluentSchemaRegistryClient


class TestSchemaRegistryClient(unittest.TestCase):
    def setUp(self):
        self.topic = 'test_topic'
        self.registry_url = 'test-url'
        self.subject = f'{self.topic}-value'
        self.schema_dispatcher_mock = MagicMock()
        self.schema_dispatcher_mock.return_value = '{"type":"record","name":"X","fields":[]}'

    @patch('kafka_messaging.schema_registry_client.confluent.SchemaRegistryClient', autospec=True)
    @patch('kafka_messaging.schema_registry_client.confluent.Schema', autospec=True)
    def test_registers_when_latest_diff_registers_and_caches(self, schema_mock, sr_client_class_mock):
        sr_client = sr_client_class_mock.return_value

        latest_schema = MagicMock()
        latest_schema.schema.schema_str = '{"type":"record","name":"Y","fields":[]}'
        latest_schema.schema_id = 7
        sr_client.get_latest_version.return_value = latest_schema
        sr_client.register_schema.return_value = 10

        client = ConfluentSchemaRegistryClient(self.registry_url, self.schema_dispatcher_mock)
        schema_id = client.register(self.topic)

        self.schema_dispatcher_mock.assert_called_once_with(self.topic)
        schema_mock.assert_called_once_with(self.schema_dispatcher_mock(self.topic), 'AVRO')
        sr_client.register_schema.assert_called_once_with(self.subject, schema_mock.return_value)
        self.assertEqual(10, schema_id)
        self.assertEqual(client._cache[self.subject], 10)

    @patch('kafka_messaging.schema_registry_client.confluent.SchemaRegistryClient', autospec=True)
    @patch('kafka_messaging.schema_registry_client.confluent.Schema', autospec=True)
    def test_registers_when_latest_same_uses_existing_id_no_register(self, schema_mock, sr_client_class_mock):
        sr_client = sr_client_class_mock.return_value

        latest_schema = MagicMock()
        latest_schema.schema.schema_str = self.schema_dispatcher_mock.return_value
        latest_schema.schema_id = 42
        sr_client.get_latest_version.return_value = latest_schema

        client = ConfluentSchemaRegistryClient(self.registry_url, self.schema_dispatcher_mock)
        schema_id = client.register(self.topic)

        self.schema_dispatcher_mock.assert_called_once_with(self.topic)
        sr_client.register_schema.assert_not_called()
        self.assertEqual(42, schema_id)
        self.assertEqual(client._cache[self.subject], 42)

    @patch('kafka_messaging.schema_registry_client.confluent.SchemaRegistryClient', autospec=True)
    @patch('kafka_messaging.schema_registry_client.confluent.Schema', autospec=True)
    def test_registers_when_subject_not_found_registers(self, schema_mock, sr_client_class_mock):
        sr_client = sr_client_class_mock.return_value

        sr_client.get_latest_version.side_effect = Exception('not found')
        sr_client.register_schema.return_value = 11

        client = ConfluentSchemaRegistryClient(self.registry_url, self.schema_dispatcher_mock)
        schema_id = client.register(self.topic)

        schema_mock.assert_called_once_with(self.schema_dispatcher_mock(self.topic), 'AVRO')
        sr_client.register_schema.assert_called_once_with(self.subject, schema_mock.return_value)
        self.assertEqual(11, schema_id)
        self.assertEqual(client._cache[self.subject], 11)

    @patch('kafka_messaging.schema_registry_client.confluent.SchemaRegistryClient', autospec=True)
    @patch('kafka_messaging.schema_registry_client.confluent.Schema', autospec=True)
    def test_cache_hit_short_circuits_registry_calls(self, schema_mock, sr_client_class_mock):
        sr_client = sr_client_class_mock.return_value

        client = ConfluentSchemaRegistryClient(self.registry_url, self.schema_dispatcher_mock)
        client._cache[self.subject] = 99

        schema_id = client.register(self.topic)

        sr_client.get_latest_version.assert_not_called()
        sr_client.register_schema.assert_not_called()
        self.assertEqual(99, schema_id)

    @patch('kafka_messaging.schema_registry_client.confluent.SchemaRegistryClient', autospec=True)
    def test_get_schema_str_by_id_delegates(self, sr_client_class_mock):
        sr_client = sr_client_class_mock.return_value
        sr_client.get_schema.return_value.schema_str = '{"type":"record","name":"Z","fields":[]}'

        client = ConfluentSchemaRegistryClient(self.registry_url, self.schema_dispatcher_mock)
        out = client.get_schema_str_by_id(123)

        sr_client.get_schema.assert_called_once_with(123)
        self.assertEqual(out, '{"type":"record","name":"Z","fields":[]}')
