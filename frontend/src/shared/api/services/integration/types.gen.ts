export const Auth = {
    IAM: 'iam',
    SECRET: 'secret',
    CERT: 'cert',
    PASSWORD_NATIVE: 'password_native',
    PASSWORD_PROXY: 'password_proxy',
    JWT: 'jwt',
} as const;
export type Auth = typeof Auth[keyof typeof Auth];

export const Cloud = {
    AWS: 'aws',
    AZURE: 'azure',
    GCP: 'gcp',
    SNOWFLAKE_MANAGED: 'snowflake_managed',
} as const;
export type Cloud = typeof Cloud[keyof typeof Cloud];


export const DB = {
    MYSQL: 'mysql',
    SQLSERVER: 'sqlserver',
    POSTGRESQL: 'postgresql',
    SNOWFLAKE: 'snowflake',
} as const;
export type DB = typeof DB[keyof typeof DB];


export type DataStoreCreateRequest = {
    auth: Auth;
    cloud: Cloud;
    db: DB;
    connection_name: string;
    host: string;
    database_name: string;
    descr: string;
    port?: number | null;
    warehouse?: string | null;
    tenant_id?: string | null;
    client_id?: string | null;
    region?: string | null;
    kek_kid?: string | null;
    azure_cert_kid?: string | null;
    azure_cert_name?: string | null;
    azure_public_key_pem?: string | null;
    snowflake_public_key_pem?: string | null;
    username?: string | null;
    password?: string | null;
    client_secret?: string | null;
    aws_role_arn?: string | null;
    aws_external_id?: string | null;
    snowflake_private_key?: string | null;
    autosync_on?: boolean | null;
};


export type DataStoreTestResponse = {
    success: boolean,
};


export type DataStoreUpdateRequest = {
    connection_name?: string | null;
    host?: string | null;
    port?: number | null;
    database_name?: string | null;
    autosync_on?: boolean | null;
};


export type DataStoreProfile = {
    id: string;
    auth: Auth;
    cloud: Cloud;
    db: DB;
    connection_name: string;
    host: string;
    database_name: string;
    port?: number | null;
    autosync_on: boolean;
};


export type LlmModelCreateRequest = {
    model_id: string;
    label: string;
    api_base: string;
    connection_params: Record<string, unknown>;
    max_tokens: number;
    kek_kid?: string | null;
}

export type LlmProfile = {
    api_base: string;
    model_id: string;
    label: string;
    max_tokens: number;
}