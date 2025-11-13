import { Auth } from './auth.interface';
import { DB } from './db.interface';
import { Cloud } from './cloud.interface';

export interface IntegrationCreateRequest {
    auth: Auth;
    cloud: Cloud;
    db: DB;
    connection_name: string;
    host: string;
    database_name: string;
    port?: number | null;
    warehouse?: string | null;
    tenant_id?: string | null;
    client_id?: string | null;
    region?: string | null;
    kek_kid?: string | null;
    azure_cert_kid?: string | null;
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
