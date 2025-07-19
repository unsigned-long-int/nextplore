import os
from contextlib import AbstractContextManager
from sqlalchemy.orm import Session

from shared.database.sql_connection_service import session_scope, fetch_session_maker, fetch_engine


def backend_session_scope() -> AbstractContextManager[Session]:
    DATABASE_URL = f'postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}'
    engine = fetch_engine(DATABASE_URL)
    session_maker = fetch_session_maker(engine)
    return session_scope(session_maker)
