import io
import json
import struct
from collections.abc import Callable
from functools import lru_cache
from typing import Any

from fastavro import parse_schema, schemaless_reader, schemaless_writer
from kafka_messaging.events.base import BaseEvent
from kafka_messaging.schema_registry_client import ConfluentSchemaRegistryClient

from .utils import to_avro_values


@lru_cache(maxsize=128)
def _parsed(schema_str: str):
    return parse_schema(json.loads(schema_str))


class AvroCodec:
    CONFLUENT_MAGIC_BYTES = b"\x00"

    def __init__(
        self,
        schema_registry_client: ConfluentSchemaRegistryClient,
        schema_dispatcher: Callable[[str], str],
    ) -> None:
        self._schema_registry_client = schema_registry_client
        self._schema_dispatcher = schema_dispatcher

    def serialize(self, topic: str, event: BaseEvent) -> bytes:
        schema_str = self._schema_dispatcher(topic)
        payload = event.model_dump()
        payload.update({"event_name": event.event_name, "version": event.version})
        payload = to_avro_values(payload)

        buf = io.BytesIO()
        buf.write(AvroCodec.CONFLUENT_MAGIC_BYTES)
        schema_id = self._schema_registry_client.register(topic)
        buf.write(struct.pack(">I", schema_id))

        parsed = _parsed(schema_str)
        schemaless_writer(buf, parsed, payload)
        return buf.getvalue()

    def deserialize(self, value: bytes) -> dict[str, Any]:
        bio = io.BytesIO(value)
        if bio.read(1) != AvroCodec.CONFLUENT_MAGIC_BYTES:
            raise ValueError("Wrong confluent format. No magic bytes found.")

        (schema_id,) = struct.unpack(">I", bio.read(4))
        schema_str = self._schema_registry_client.get_schema_str_by_id(schema_id)
        writer_schema = _parsed(schema_str)
        return schemaless_reader(bio, writer_schema)
