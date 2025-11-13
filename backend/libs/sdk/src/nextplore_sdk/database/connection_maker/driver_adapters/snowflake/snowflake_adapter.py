import snowflake.connector
from typing import ClassVar, Optional, Dict, Any

from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import DriverAdapter


class SnowflakeAdapter(DriverAdapter):
    DIALECT: ClassVar[str] = 'snowflake://'

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
        if 'warehouse' not in kwargs:
            raise AttributeError('Warehouse must be provided.')

        conn = snowflake.connector.connect(
            account=host,
            user=username,
            password=password,
            warehouse=kwargs['warehouse'],
            database=database,
            timeout=timeout
        )
        return conn