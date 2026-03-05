import logging
import time
from typing import Callable, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from nextplore_sdk.database.connection_maker.exc.exceptions import ConnectionFailed

logger = logging.getLogger(__name__)


def invoke_engine(
    dialect: str,
    creator: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: int = 2,
    **invoker_kwargs: Any
) -> Engine:
    attempt = 0
    while attempt <= max_retries:
        try:
            engine = create_engine(
                dialect,
                creator=creator,
                **invoker_kwargs
            )
            with engine.connect() as conn:
                conn.execute(text('SELECT 1;'))
            logger.info(f'Connection succeeded after {attempt + 1} attempt.')
            return engine
        except OperationalError as e:
            logger.warning(f'Connection attempt {attempt + 1} failed.')
            attempt += 1
            if attempt > max_retries:
                logger.error(f'Connection failed after {max_retries} retries.', exc_info=True)
                raise ConnectionFailed('Connection failed after retries.') from e

            delay = base_delay * (backoff_factor ** (attempt - 1))
            logger.info(f'Retrying in {delay:.2f} seconds...')
            time.sleep(delay)
        except Exception as e:
            logger.error('Unexpected error during test connection.', exc_info=True)
            raise ConnectionFailed('Unexpected connection failure.') from e
