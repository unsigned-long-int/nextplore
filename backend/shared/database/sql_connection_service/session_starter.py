import logging
import time
from typing import Iterator
from contextlib import contextmanager
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker, scoped_session


logger = logging.getLogger(__name__)


class ConnectionFailed(Exception):
    pass


def fetch_engine(
    sql_connection_string: str, 
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: int = 2,
    **kwargs
) -> Engine:
    attempt = 0
    while attempt <= max_retries:
        try:
            engine = create_engine(sql_connection_string, **kwargs)
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            logger.info(f'Connection succeeded after {attempt + 1} attempt.')
            return engine
        except OperationalError as e:
            logger.warning(f'Connection attempt {attempt + 1} failed.')
            attempt += 1
            if attempt > max_retries:
                logger.error(f'Connection failed after {max_retries} retries.')
                raise ConnectionFailed(f'Connection failed after retries') from e
            
            delay = base_delay * (backoff_factor ** (attempt - 1))
            logger.info(f'Retrying in {delay:.2f} seconds...')
            time.sleep(delay)
        except Exception as e:
            logger.exception('Unexpected error during test connection.')
            raise ConnectionFailed('Unexpected connection failure.') from e


def fetch_session_maker(engine: Engine) -> scoped_session[Session]:
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)

@contextmanager
def session_scope(scoped_session_factory: scoped_session[Session]) -> Iterator[Session]:
    session = scoped_session_factory()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        scoped_session_factory.remove()