from enum import Enum


class SecretType(str, Enum):
    USERNAME = 'username'
    PASSWORD = 'password'
    CLIENT_SECRET = 'client_secret'
    AWS_ROLE_ARN = 'aws_role_arn'
    AWS_EXTERNAL_ID = 'aws_external_id'
    SNOWFLAKE_PRIVATE_KEY = 'snowflake_private_key'
    