from enum import Enum


class DB(Enum):
    MYSQL = 'mysql'
    SQLSERVER = 'sqlserver'
    POSTGRESQL = 'postgresql'
    SNOWFLAKE = 'snowflake'
