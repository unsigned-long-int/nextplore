import ssl
from typing import Any, ClassVar

import pymysql
from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import (
    DriverAdapter,
)


class MysqlPyMysqlAdapter(DriverAdapter):
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
        ctx = (
            ssl.create_default_context(cafile=ca_path)
            if ca_path
            else ssl.create_default_context()
        )
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        return pymysql.connect(
            host=host,
            port=port,
            db=database,
            user=username,
            password=password,
            ssl=ctx,
            connect_timeout=timeout,
        )
