export interface IntegrationUpdateRequest {
    connection_name?: string | null;
    host?: string | null;
    port?: number | null;
    database_name?: string | null;
    autosync_on?: boolean | null;
};
