from typing import Dict

from nextplore_sdk.database.connection_maker.exc.exceptions import MissingAuth
from nextplore_sdk.database.connection_maker.models.auth import Auth


AUTH_MAP: Dict[str, Auth] = {
    'iam': Auth.IAM,
    'secret': Auth.SECRET,
    'cert': Auth.CERT,
    'password_native': Auth.PASSWORD_NATIVE,
    'password_proxy': Auth.PASSWORD_PROXY,
    'jwt': Auth.JWT
}


def to_domain_auth(auth: str) -> Auth:
    try:
        return AUTH_MAP[auth]
    except KeyError:
        raise MissingAuth(f'Auth not found in map: {auth}')
