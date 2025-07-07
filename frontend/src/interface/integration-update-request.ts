export interface IntegrationUpdateRequest {
    id: string;
    service_type?: string;
    auth_method?: string;
    connection_name?: string;
    host?: string;
    port?: number;
    database_name?: string;
    username?: string;
    password?: string;
    kerberos_principal?: string;
    windows_domain?: string;
    extra_options?: string;
    autosync_on?: boolean;
};
