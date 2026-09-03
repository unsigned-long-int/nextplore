from enum import Enum


class Auth(Enum):
    IAM = "iam"
    SECRET = "secret"
    CERT = "cert"
    PASSWORD_NATIVE = "password_native"
    PASSWORD_PROXY = "password_proxy"
    JWT = "jwt"
