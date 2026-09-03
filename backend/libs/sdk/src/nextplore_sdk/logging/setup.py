import logging.config
from pathlib import Path
from typing import Any

from nextplore_sdk.logging.custom_json_formatter import CustomJsonFormatter


def setup_logger(service_meta: dict[str, Any], config_path: Path) -> None:
    logging.config.fileConfig(config_path, disable_existing_loggers=False)
    for handler in logging.root.handlers:
        formatter = getattr(handler, "formatter", None)
        if isinstance(formatter, CustomJsonFormatter):
            formatter.service_meta.update(service_meta)
