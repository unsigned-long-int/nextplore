import ssl
import pymysql
from typing import ClassVar, Optional, Dict, Any

from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import DriverAdapter


class MysqlPyMysqlAdapter(DriverAdapter):
    DIALECT: ClassVar[str] = 'mysql+pymysql://'

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
        ctx = ssl.create_default_context(cafile=ca_path) if ca_path else ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        return pymysql.connect(
            host=host, 
            port=port, 
            db=database, 
            user=username, 
            password=password,
            ssl=ctx, 
            connect_timeout=timeout
        )