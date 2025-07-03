import os

from datetime import datetime, timezone
from pythonjsonlogger.json import JsonFormatter

from _version import version, app_name

env = os.getenv('ENV', 'dev').lower()


class CustomJsonFormatter(JsonFormatter):
    def __init__(self, *args, **kwargs) -> None:
        rename_fields = {
            'asctime': 'timestamp',
            'levelname': 'level'
        }
        self.job_run_timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(*args, rename_fields=rename_fields, **kwargs)

    def add_fields(self, log_record, record, message_dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record['app_name'] = app_name
        log_record['version'] = version
        log_record['env'] = env
        log_record['job_run_timestamp'] = self.job_run_timestamp