from typing import Iterator
from contextlib import contextmanager
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker, scoped_session


def fetch_engine(sql_connection_string: str, **kwargs) -> Engine:
    return create_engine(sql_connection_string, **kwargs)

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