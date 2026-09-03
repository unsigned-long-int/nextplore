from nextplore_sdk.database.connection_maker.exc.exceptions import MissingDB
from nextplore_sdk.database.connection_maker.models.db import DB

DB_MAP: dict[str, DB] = {
    "mysql": DB.MYSQL,
    "sqlserver": DB.SQLSERVER,
    "postgresql": DB.POSTGRESQL,
    "snowflake": DB.SNOWFLAKE,
}


def to_domain_db(db: str) -> DB:
    try:
        return DB_MAP[db]
    except KeyError:
        raise MissingDB(f"DB not found in map: {db}")
