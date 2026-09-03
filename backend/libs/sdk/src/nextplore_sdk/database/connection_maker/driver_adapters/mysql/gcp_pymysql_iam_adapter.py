from typing import Any, ClassVar

from google.cloud.sql.connector import IPTypes
from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import (
    DriverAdapter,
)
from nextplore_sdk.database.connection_maker.utils.gcp_cloud_sql_connector import (
    GcpCloudSqlConnector,
)


class GcpMysqlPyMysqlIamAdapter(DriverAdapter):
    DIALECT: ClassVar[str] = "mysql+pymysql://"

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
        connector = GcpCloudSqlConnector.get()
        conn = connector.connect(
            host,
            driver="pymysql",
            user=username,
            db=database,
            enable_iam_auth=True,
            ip_type=IPTypes.PUBLIC,
            timeout=timeout,
            port=port,
        )
        return conn
