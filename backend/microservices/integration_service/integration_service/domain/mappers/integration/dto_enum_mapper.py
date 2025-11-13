from typing import Dict

from integration_service.domain.exceptions import (
    MissingAuth,
    MissingCloud,
    MissingDB
)
from integration_service.api.models.auth import Auth
from integration_service.api.models.db import DB
from integration_service.api.models.cloud import Cloud


AUTH_DTO_MAP: Dict[str, Auth] = {
    'iam': Auth.IAM,
    'secret': Auth.SECRET,
    'cert': Auth.CERT,
    'password_native': Auth.PASSWORD_NATIVE,
    'password_proxy': Auth.PASSWORD_PROXY,
    'jwt': Auth.JWT
}

DB_DTO_MAP: Dict[str, DB] = {
    'mysql': DB.MYSQL,
    'postgres': DB.POSTGRESQL,
    'sqlserver': DB.SQLSERVER,
    'snowflake': DB.SNOWFLAKE,
}

CLOUD_DTO_MAP: Dict[str, Cloud] = {
    'aws': Cloud.AWS,
    'azure': Cloud.AZURE,
    'gcp': Cloud.GCP,
    'snowflake_managed': Cloud.SNOWFLAKE_MANAGED
}


def to_dto_auth(auth: str) -> Auth:
    try:
        return AUTH_DTO_MAP[auth]
    except KeyError:
        raise MissingAuth(f'Auth not found in map: {auth}')


def to_dto_db(db: str) -> DB:
    try:
        return DB_DTO_MAP[db]
    except KeyError:
        raise MissingDB(f'DB not found in map: {db}')


def to_dto_cloud(cloud: str) -> Cloud:
    try:
        return CLOUD_DTO_MAP[cloud]
    except KeyError:
        raise MissingCloud(f'Cloud not found in map: {cloud}')
