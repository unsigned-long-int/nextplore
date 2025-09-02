export enum Auth {
    IAM = 'iam',
    SECRET = 'secret',
    CERT = 'cert',
    PASSWORD_NATIVE = 'password_native',
    PASSWORD_PROXY = 'password_proxy',
    JWT = 'jwt'
} 

export enum Cloud {
    AWS = 'aws',
    AZURE = 'azure',
    GCP = 'gcp',
    SNOWFLAKE_MANAGED = 'snowflake_managed'
}

export enum DB {
    MYSQL = 'mysql',
    SQLSERVER = 'sqlserver',
    POSTGRESQL = 'postgresql',
    SNOWFLAKE = 'snowflake'
}


export interface IntegrationCreateRequest {
    auth: Auth;
    cloud: Cloud;
    db: DB;
    connection_name: string;
    host: string;
    database_name: string;
    warehouse?: string | null;
    tenant_id?: string | null;
    client_id?: string | null;
    region?: string | null;
    port?: number | null;
    azure_cert_kid?: string | null;
    azure_public_key_pem?: string | null;
    snowflake_public_key_pem?: string | null;
    username?: string | null;
    password?: string | null;
    secret?: string | null;
    aws_role_arn?: string | null;
    aws_external_id?: string | null;
    autosync_on?: boolean | null;
};

export interface IntegrationFormProps {
    service_type: string;
    onSubmit: (values: IntegrationCreateRequest) => void;
};