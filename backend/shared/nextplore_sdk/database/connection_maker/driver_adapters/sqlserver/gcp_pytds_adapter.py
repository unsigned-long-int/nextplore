from typing import ClassVar, Optional, Dict, Any
from google.cloud.sql.connector import IPTypes

from connection_maker.utils.gcp_cloud_sql_connector import GcpCloudSqlConnector
from connection_maker.driver_adapters.driver_adapter import DriverAdapter


class GcpSqlserverPyTdsAdapter(DriverAdapter):
    DIALECT: ClassVar[str] = 'mssql+pytds://'

    def connect(
        self, 
        host: str, 
        database: str, 
        port: Optional[int] = None, 
        username: Optional[str] = None, 
        password: Optional[str] = None,
        ca_path: Optional[str] = None,
        timeout: int = 10,
        attrs_before: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        connector = GcpCloudSqlConnector.get('/Users/nik/Downloads/nextplore-470323-18ec66288496.json')
        conn = connector.connect(
            host,
            driver='pytds',
            user=username,
            password=password,
            db=database,
            ip_type=IPTypes.PUBLIC,
            cafile=ca_path,
            validate_host=False,
            timeout=timeout,
            port=port
        )
        return conn
