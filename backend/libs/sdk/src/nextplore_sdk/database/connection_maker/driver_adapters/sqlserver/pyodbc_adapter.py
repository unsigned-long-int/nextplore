import pyodbc
from typing import Dict, Any, ClassVar, Optional

from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import DriverAdapter


class SqlserverPyOdbcAdapter(DriverAdapter):
    DIALECT: ClassVar[str] = 'mssql+pyodbc://'

    def connect(
        self, 
        host: str, 
        database: str, 
        port: Optional[int] = None, 
        username: Optional[str] = None, 
        password: Optional[str] = None,
        ca_path: Optional[str] = None,
        timeout: int = 10,
        attrs_before: Optional[Dict[Any, Any]] = None,
        **kwargs: Any
    ):
        if not attrs_before:
            con = (
                'Driver={ODBC Driver 18 for SQL Server};'
                f'Server=tcp:{host},{port};'
                f'UID={username};'
                f'PWD={password};'
                f'Database={database};'
                'Encrypt=Yes;'
                'TrustServerCertificate=No;'
                f'LoginTimeout={timeout};'
            )
            return pyodbc.connect(con)
        
        con = (
                'Driver={ODBC Driver 18 for SQL Server};'
                f'Server=tcp:{host},{port};'
                f'Database={database};'
                'Encrypt=Yes;'
                'TrustServerCertificate=No;'
                f'LoginTimeout={timeout};'
            )
        return pyodbc.connect(
            con,
            attrs_before=attrs_before
        )
