from typing import Any, ClassVar

import pyodbc
from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import (
    DriverAdapter,
)


class SqlserverPyOdbcAdapter(DriverAdapter):
    DIALECT: ClassVar[str] = "mssql+pyodbc://"

    def connect(
        self,
        host: str,
        database: str,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        ca_path: str | None = None,
        timeout: int = 10,
        attrs_before: dict[Any, Any] | None = None,
        **kwargs: Any,
    ):
        if not attrs_before:
            con = (
                "Driver={ODBC Driver 18 for SQL Server};"
                f"Server=tcp:{host},{port};"
                f"UID={username};"
                f"PWD={password};"
                f"Database={database};"
                "Encrypt=Yes;"
                "TrustServerCertificate=No;"
                f"LoginTimeout={timeout};"
            )
            return pyodbc.connect(con)

        con = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server=tcp:{host},{port};"
            f"Database={database};"
            "Encrypt=Yes;"
            "TrustServerCertificate=No;"
            f"LoginTimeout={timeout};"
        )
        return pyodbc.connect(con, attrs_before=attrs_before)
