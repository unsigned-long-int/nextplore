from typing import Any, ClassVar

import psycopg2
from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import (
    DriverAdapter,
)


class PostgresqlPsycopg2Adapter(DriverAdapter):
    DIALECT: ClassVar[str] = "postgresql+psycopg2://"

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
        return psycopg2.connect(
            host=host,
            port=port,
            dbname=database,
            user=username,
            password=password,
            sslmode="verify-full",
            sslrootcert=ca_path,
            connect_timeout=timeout,
        )
