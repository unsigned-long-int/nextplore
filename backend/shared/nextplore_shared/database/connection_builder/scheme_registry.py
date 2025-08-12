from typing import Dict


SCHEME_REGISTRY: Dict[str, str] = {
    'postgresql': 'postgresql+psycopg2',
    'mysql': 'mysql+pymysql',
    'sqlserver': 'mssql+pyodbc',
    'snowflake': 'snowflake',
}