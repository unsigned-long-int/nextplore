from nextplore_sdk.database.connection_maker.auth.auth_strategy import AuthStrategy
from nextplore_sdk.database.connection_maker.auth.azure_asql_strategy import (
    AzureIamAsqlStrategy,
)
from nextplore_sdk.database.connection_maker.auth.credential_auth_strategy import (
    CredentialAuthStrategy,
)
from nextplore_sdk.database.connection_maker.auth.iam_request_signing_auth_strategy import (
    IamRequestSigningAuthStrategy,
)
from nextplore_sdk.database.connection_maker.auth.snowflake_auth_strategy import (
    SnowflakeAuthStrategy,
)
from nextplore_sdk.database.connection_maker.auth.snowflake_jwt_auth_strategy import (
    SnowflakeJwtAuthStrategy,
)
from nextplore_sdk.database.connection_maker.credentials_providers.aws_role_credentials_provider import (
    AWSRoleCredentialsProvider,
)
from nextplore_sdk.database.connection_maker.credentials_providers.azure_cert_credentials_provider import (
    AzureCertCredentialsProvider,
)
from nextplore_sdk.database.connection_maker.credentials_providers.azure_secret_credentials_provider import (
    AzureSecretCredentialsProvider,
)
from nextplore_sdk.database.connection_maker.credentials_providers.credentials_provider import (
    CredentialsProvider,
)
from nextplore_sdk.database.connection_maker.credentials_providers.native_password_credentials_provider import (
    NativePasswordCredentialsProvider,
)
from nextplore_sdk.database.connection_maker.credentials_providers.snowflake_private_key_credentials_provider import (
    SnowflakePrivateKeyCredentialsProvider,
)
from nextplore_sdk.database.connection_maker.credentials_providers.snowflake_secret_credentials_provider import (
    SnowflakeSecretCredentialsProvider,
)
from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import (
    DriverAdapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.mysql.gcp_pymysql_adapter import (
    GcpMysqlPyMysqlAdapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.mysql.gcp_pymysql_iam_adapter import (
    GcpMysqlPyMysqlIamAdapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.mysql.pymysql_adapter import (
    MysqlPyMysqlAdapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.postgresql.gcp_pg8000_adapter import (
    GcpPostgresqlPg8000Adapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.postgresql.gcp_pg8000_iam_adapter import (
    GcpPostgresqlPg8000IamAdapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.postgresql.psycopg2_adapter import (
    PostgresqlPsycopg2Adapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_adapter import (
    SnowflakeAdapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.snowflake.snowflake_jwt_adapter import (
    SnowflakeJwtAdapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.sqlserver.gcp_pytds_adapter import (
    GcpSqlserverPyTdsAdapter,
)
from nextplore_sdk.database.connection_maker.driver_adapters.sqlserver.pyodbc_adapter import (
    SqlserverPyOdbcAdapter,
)
from nextplore_sdk.database.connection_maker.models.auth import Auth
from nextplore_sdk.database.connection_maker.models.cloud import Cloud
from nextplore_sdk.database.connection_maker.models.db import DB

STRATEGY_REGISTRY: dict[
    tuple[Cloud, DB, Auth],
    tuple[type[AuthStrategy], type[DriverAdapter], type[CredentialsProvider] | None],
] = {
    (Cloud.AZURE, DB.MYSQL, Auth.SECRET): (
        CredentialAuthStrategy,
        MysqlPyMysqlAdapter,
        AzureSecretCredentialsProvider,
    ),
    (Cloud.AZURE, DB.POSTGRESQL, Auth.SECRET): (
        CredentialAuthStrategy,
        PostgresqlPsycopg2Adapter,
        AzureSecretCredentialsProvider,
    ),
    (Cloud.AZURE, DB.MYSQL, Auth.CERT): (
        CredentialAuthStrategy,
        MysqlPyMysqlAdapter,
        AzureCertCredentialsProvider,
    ),
    (Cloud.AZURE, DB.POSTGRESQL, Auth.CERT): (
        CredentialAuthStrategy,
        PostgresqlPsycopg2Adapter,
        AzureCertCredentialsProvider,
    ),
    (Cloud.AZURE, DB.SQLSERVER, Auth.SECRET): (
        AzureIamAsqlStrategy,
        SqlserverPyOdbcAdapter,
        AzureSecretCredentialsProvider,
    ),
    (Cloud.AZURE, DB.SQLSERVER, Auth.CERT): (
        AzureIamAsqlStrategy,
        SqlserverPyOdbcAdapter,
        AzureCertCredentialsProvider,
    ),
    (Cloud.AZURE, DB.MYSQL, Auth.PASSWORD_NATIVE): (
        CredentialAuthStrategy,
        MysqlPyMysqlAdapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.AZURE, DB.POSTGRESQL, Auth.PASSWORD_NATIVE): (
        CredentialAuthStrategy,
        PostgresqlPsycopg2Adapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.AZURE, DB.SQLSERVER, Auth.PASSWORD_NATIVE): (
        CredentialAuthStrategy,
        SqlserverPyOdbcAdapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.AWS, DB.MYSQL, Auth.PASSWORD_NATIVE): (
        CredentialAuthStrategy,
        MysqlPyMysqlAdapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.AWS, DB.POSTGRESQL, Auth.PASSWORD_NATIVE): (
        CredentialAuthStrategy,
        PostgresqlPsycopg2Adapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.AWS, DB.SQLSERVER, Auth.PASSWORD_NATIVE): (
        CredentialAuthStrategy,
        SqlserverPyOdbcAdapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.AWS, DB.MYSQL, Auth.IAM): (
        CredentialAuthStrategy,
        MysqlPyMysqlAdapter,
        AWSRoleCredentialsProvider,
    ),
    (Cloud.AWS, DB.POSTGRESQL, Auth.IAM): (
        CredentialAuthStrategy,
        PostgresqlPsycopg2Adapter,
        AWSRoleCredentialsProvider,
    ),
    (Cloud.GCP, DB.SQLSERVER, Auth.PASSWORD_NATIVE): (
        CredentialAuthStrategy,
        SqlserverPyOdbcAdapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.GCP, DB.SQLSERVER, Auth.PASSWORD_PROXY): (
        CredentialAuthStrategy,
        GcpSqlserverPyTdsAdapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.GCP, DB.POSTGRESQL, Auth.PASSWORD_NATIVE): (
        CredentialAuthStrategy,
        PostgresqlPsycopg2Adapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.GCP, DB.POSTGRESQL, Auth.PASSWORD_PROXY): (
        CredentialAuthStrategy,
        GcpPostgresqlPg8000Adapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.GCP, DB.MYSQL, Auth.PASSWORD_NATIVE): (
        CredentialAuthStrategy,
        MysqlPyMysqlAdapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.GCP, DB.MYSQL, Auth.PASSWORD_PROXY): (
        CredentialAuthStrategy,
        GcpMysqlPyMysqlAdapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.GCP, DB.POSTGRESQL, Auth.IAM): (
        IamRequestSigningAuthStrategy,
        GcpPostgresqlPg8000IamAdapter,
        None,
    ),
    (Cloud.GCP, DB.MYSQL, Auth.IAM): (
        IamRequestSigningAuthStrategy,
        GcpMysqlPyMysqlIamAdapter,
        None,
    ),
    (Cloud.SNOWFLAKE_MANAGED, DB.SNOWFLAKE, Auth.PASSWORD_NATIVE): (
        SnowflakeAuthStrategy,
        SnowflakeAdapter,
        NativePasswordCredentialsProvider,
    ),
    (Cloud.SNOWFLAKE_MANAGED, DB.SNOWFLAKE, Auth.SECRET): (
        SnowflakeAuthStrategy,
        SnowflakeAdapter,
        SnowflakeSecretCredentialsProvider,
    ),
    (Cloud.SNOWFLAKE_MANAGED, DB.SNOWFLAKE, Auth.JWT): (
        SnowflakeJwtAuthStrategy,
        SnowflakeJwtAdapter,
        SnowflakePrivateKeyCredentialsProvider,
    ),
}
