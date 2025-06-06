from urllib.parse import quote_plus

from api.models import IntegrationCreateRequest


def build_connection_string(integration_create_request: IntegrationCreateRequest) -> str:
    stype = integration_create_request.service_type.lower()
    scheme_map = {
        'postgresql': 'postgresql+psycopg2',
        'mysql': 'mysql+pymysql',
        'sqlserver': 'mssql+pyodbc',
        'snowflake': 'snowflake',
    }

    scheme = scheme_map.get(stype)
    if not scheme:
        raise ValueError(f'Unsupported service type: {stype}')

    auth = ''
    if integration_create_request.auth_method == 'basic' and integration_create_request.username and integration_create_request.password:
        auth = f'{quote_plus(integration_create_request.username)}:{quote_plus(integration_create_request.password)}@'
    elif integration_create_request.auth_method == 'windows' and integration_create_request.username and integration_create_request.windows_domain:
        domain_user = f'{integration_create_request.windows_domain}\\{integration_create_request.username}'
        auth = f'{quote_plus(domain_user)}:{quote_plus(integration_create_request.password or '')}@'
    elif integration_create_request.auth_method == 'kerberos':
        auth = ''
    else:
        auth = ''

    host = integration_create_request.host
    port = integration_create_request.port
    db = integration_create_request.database_name or ''

    query = ''
    if integration_create_request.extra_options:
        query = '&'.join(
            f'{quote_plus(str(k))}={quote_plus(str(v))}'
            for k, v in integration_create_request.extra_options.items()
        )
        query = f'?{query}'

    if stype == 'snowflake':
        account = host
        schema = integration_create_request.extra_options.get('schema', '') if integration_create_request.extra_options else ''
        db_path = f'/{db}/{schema}' if schema else f'/{db}'
        return f'{scheme}://{auth}{account}{db_path}{query}'

    if stype == 'sqlserver':
        query = query or '?driver=ODBC+Driver+17+for+SQL+Server'

    return f'{scheme}://{auth}{host}:{port}/{db}{query}'