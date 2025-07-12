import os
import logging.config


def setup_logger() -> None:
    env = os.getenv('ENV', 'prod').lower()
    config_file = (
        'config/logging-dev.conf' if env == 'local' else 'config/logging-prod.conf'
    )
    if env == 'local':
        os.makedirs('./logs', exist_ok=True)
    logging.config.fileConfig(config_file, disable_existing_loggers=False)