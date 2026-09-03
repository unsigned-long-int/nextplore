import os
import threading

from google.cloud.sql.connector import Connector
from google.oauth2 import service_account


class GcpCloudSqlConnector:
    _lock = threading.RLock()
    _connector: Connector | None = None
    _creds_path: str | None = None

    @classmethod
    def get(cls, credentials_path: str = os.getenv("GCP_ACCESS_KEY")) -> Connector:
        with cls._lock:
            if cls._connector is not None:
                return cls._connector

            creds = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            cls._connector = Connector(credentials=creds)
            cls._creds_path = credentials_path
            return cls._connector

    @classmethod
    def close(cls) -> None:
        with cls._lock:
            if cls._connector is not None:
                try:
                    cls._connector.close()
                finally:
                    cls._connector = None
                    cls._creds_path = None
