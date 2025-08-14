import json

from typing import Dict, Callable
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.schema_registry_client import Schema


class ConfluentSchemaRegistryClient:
    def __init__(self, registry_url: str, schema_dispatcher: Callable[[str], str]) -> None:
        self._registry = SchemaRegistryClient({'url': registry_url})
        self._schema_dispatcher = schema_dispatcher
        self._cache: Dict[str, int] = {}

    def register(self, topic: str) -> int:
        subject = f'{topic}-value'
        schema_str = self._schema_dispatcher(topic)

        if subject in self._cache:
            return self._cache[subject]
        
        try:
            latest_schema = self._registry.get_latest_version(subject)
            latest_schema_str = latest_schema.schema.schema_str
            if json.loads(latest_schema_str) == json.loads(schema_str):
                self._cache[subject] = latest_schema.schema_id
                return latest_schema.schema_id
            schema_id = self._registry.register_schema(subject, Schema(schema_str, 'AVRO'))
            self._cache[subject] = schema_id
            return schema_id
        except Exception:
            schema_id = self._registry.register_schema(subject, Schema(schema_str, 'AVRO'))
            self._cache[subject] = schema_id
            return schema_id

    def get_schema_str_by_id(self, schema_id: int) -> str:
        return self._registry.get_schema(schema_id).schema_str