import os
from datetime import datetime, timezone
from typing import Any

from pythonjsonlogger.json import JsonFormatter

env = os.getenv("ENV", "dev").lower()


class CustomJsonFormatter(JsonFormatter):
    def __init__(self, fmt=None, datefmt=None, style="%", *args, **kwargs) -> None:
        rename_fields = {"asctime": "timestamp", "levelname": "level"}
        self.job_run_timestamp = datetime.now(timezone.utc).isoformat()
        self.service_meta: dict[str, Any] = {}
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            rename_fields=rename_fields,
            *args,
            **kwargs,
        )

    def add_fields(self, log_record, record, message_dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["env"] = env
        log_record["job_run_timestamp"] = self.job_run_timestamp
        for k, v in self.service_meta.items():
            log_record[k] = v
