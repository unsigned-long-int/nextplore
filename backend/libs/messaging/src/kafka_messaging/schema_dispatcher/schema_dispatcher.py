from .avro_schema_registry import AVRO_SCHEMA_REGISTRY


class MissingAVROSchemaForTopic(Exception):
    pass


def dispatch_schema(topic: str) -> str:
    path = AVRO_SCHEMA_REGISTRY.get(topic)
    if path is None:
        raise MissingAVROSchemaForTopic(
            f"AVRO schema definition not found for topic: {topic}"
        )

    return path.read_text()
