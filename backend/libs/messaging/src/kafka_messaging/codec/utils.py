from datetime import datetime, timezone
from uuid import UUID
from typing import Any


def _dt_to_micros(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp() * 1_000_000)


def to_avro_values(value: Any) -> Any:
    if isinstance(value, UUID): return str(value)
    if isinstance(value, datetime): return _dt_to_micros(value)
    if isinstance(value, list): return [to_avro_values(v) for v in value]
    if isinstance(value, dict): return {str(k): to_avro_values(v) for k, v in value.items()}
    return value
