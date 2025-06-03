from contextlib import AbstractContextManager
from sqlalchemy.orm import Session

from services.sql_connection_service import session_scope, fetch_session_maker, fetch_engine

def backend_session_scope() -> AbstractContextManager[Session]:
    engine = fetch_engine('')
    session_maker = fetch_session_maker(engine)
    return session_scope(session_maker)