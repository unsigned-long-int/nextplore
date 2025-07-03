export interface IntegrationCreateRequest {
    service_type: string;
    auth_method: string;
    connection_name: string;
    host: string;
    port: number;
    database_name: string;
    username: string | null;
    password: string | null;
    kerberos_principal: string | null;
    windows_domain: string | null;
    extra_options: string | null;
};

export interface IntegrationFormProps {
    service_type: string;
    onSubmit: (values: IntegrationCreateRequest) => void;
};