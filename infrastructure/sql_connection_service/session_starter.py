from sqlalchemy import Engine, create_engine


class SQLEngineGnerationError(Exception):
    pass


def fetch_engine(sql_connection_string: str) -> Optional[Engine]:
    try:
        return create_engine(sql_connection_string)
    except Exception as e:
        pass
