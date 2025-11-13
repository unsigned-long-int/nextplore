from typing import ClassVar, Optional, Dict, Any
from google.cloud.sql.connector import IPTypes

from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import DriverAdapter
from nextplore_sdk.database.connection_maker.utils.gcp_cloud_sql_connector import GcpCloudSqlConnector


class GcpMysqlPyMysqlIamAdapter(DriverAdapter):
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
        connector = GcpCloudSqlConnector.get('/Users/nik/Downloads/nextplore-470323-18ec66288496.json')
        conn = connector.connect(
            host,
            driver='pymysql',
            user=username,
            db=database,
            enable_iam_auth=True,
            ip_type=IPTypes.PUBLIC,
            timeout=timeout,
            port=port
        )
        return conn
