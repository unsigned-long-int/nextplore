import psycopg2
from typing import ClassVar, Optional, Dict, Any

from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import DriverAdapter


class PostgresqlPsycopg2Adapter(DriverAdapter):
    DIALECT: ClassVar[str] = 'postgresql+psycopg2://'

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
        return psycopg2.connect(
            host=host, 
            port=port, 
            dbname=database, 
            user=username, 
            password=password,
            sslmode='verify-full', 
            sslrootcert=ca_path, 
            connect_timeout=timeout
        )