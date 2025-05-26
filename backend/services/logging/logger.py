import logging
import os

from logging.handlers import RotatingFileHandler


def setup_logger(log_file: str = './logs/app.log') -> None:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
        ]
    )
