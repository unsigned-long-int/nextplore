import unittest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
import io
import struct

from kafka_messaging.codec.avro import AvroCodec, _parsed


class TestModel(BaseModel):
    event_name: str
    version: str
    connection_name: str
    port: int

class TestAvroCodec(unittest.TestCase):
    def setUp(self):
        self.schema_str = '''{
            "type": "record",
            "namespace": "com.nextplore.data_store",
            "name": "IntegrationCreated",
            "fields": [
                {"name": "event_name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "event_id", "type": {"type": "string", "logicalType": "uuid"}},
                {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-micros"}},
                {"name": "user_id", "type": {"type": "string", "logicalType": "uuid"}},
                {"name": "organization_id", "type": {"type": "string", "logicalType": "uuid"}},
                {"name": "integration_id", "type": {"type": "string", "logicalType": "uuid"}}
            ]
        }
        '''
        self.topic = 'Connection.Created'
        self.event = TestModel(
            event_name='test-event',
            version='1.0.0',
            connection_name='test-connection',
            port=1433
        )
        self.schema_registry_client_mock = MagicMock()
        self.schema_id = 25
        self.schema_registry_client_mock.register.return_value = self.schema_id
        self.schema_registry_client_mock.get_schema_str_by_id.return_value = self.schema_str
        self.schema_dispatcher_mock = MagicMock()
        self.schema_dispatcher_mock.return_value = self.schema_str
        self.avro_codec = AvroCodec(
            self.schema_registry_client_mock,
            self.schema_dispatcher_mock
        )

    @patch('kafka_messaging.codec.avro.schemaless_writer')
    def test_serializes_and_returns_bytes(self, schemaless_writer_mock):
        avro_serialized = self.avro_codec.serialize(self.topic, self.event)
        self.assertIn(self.avro_codec.CONFLUENT_MAGIC_BYTES, avro_serialized)
        self.schema_dispatcher_mock.assert_called_once_with(self.topic)
        self.schema_registry_client_mock.register.assert_called_once_with(self.topic)
        schemaless_writer_mock.assert_called_once()
        args, kwargs = schemaless_writer_mock.call_args
        self.assertIsInstance(args[0], io.BytesIO)
        self.assertIsNotNone(args[1])
        self.assertIsInstance(args[2], dict)

    @patch('kafka_messaging.codec.avro.to_avro_values')
    @patch('kafka_messaging.codec.avro.schemaless_writer')
    def test_serialize_calls_to_avro_values_with_enriched_payload(self, schemaless_writer_mock, to_avro_values_mock):
        to_avro_values_mock.side_effect = lambda d: d
        _ = self.avro_codec.serialize(self.topic, self.event)

        to_avro_values_mock.assert_called_once()
        (payload_arg,), _ = to_avro_values_mock.call_args
        self.assertEqual(payload_arg['event_name'], self.event.event_name)
        self.assertEqual(payload_arg['version'], self.event.version)

    @patch('kafka_messaging.codec.avro.schemaless_reader', return_value={'ok': True})
    def test_deserialize_reads_using_schema_from_registry(self, schemaless_reader_mock):
        buf = io.BytesIO()
        buf.write(AvroCodec.CONFLUENT_MAGIC_BYTES)
        buf.write(struct.pack('>I', self.schema_id))
        payload = buf.getvalue()

        result = self.avro_codec.deserialize(payload)

        self.schema_registry_client_mock.get_schema_str_by_id.assert_called_once_with(self.schema_id)
        schemaless_reader_mock.assert_called_once()
        reader_args, _ = schemaless_reader_mock.call_args
        self.assertIsInstance(reader_args[0], io.BytesIO)
        self.assertDictEqual(result, {'ok': True})


    def test_deserialize_raises_on_wrong_magic_bytes(self):
        bad_payload = b'\x01' + struct.pack('>I', self.schema_id) + b'rest'
        with self.assertRaisesRegex(ValueError, 'Wrong confluent format'):
            self.avro_codec.deserialize(bad_payload)

    def test_parsed_caches_parsed_schema(self):
        with patch('kafka_messaging.codec.avro.parse_schema') as parse_schema_mock:
            _parsed.cache_clear()
            _parsed(self.schema_str)
            _parsed(self.schema_str)
            parse_schema_mock.assert_called_once()
