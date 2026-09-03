import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

logger = logging.getLogger(__name__)


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
