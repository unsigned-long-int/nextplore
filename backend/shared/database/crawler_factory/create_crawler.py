from sqlalchemy import inspect
from sqlalchemy.engine.reflection import Inspector
from shared.database.sql_connection_service import fetch_engine


def get_crawler(sql_connection_string: str) -> Inspector:
    engine = fetch_engine(sql_connection_string)
    inspector = inspect(engine)
    return inspector
