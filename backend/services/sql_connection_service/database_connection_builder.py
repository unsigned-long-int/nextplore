from urllib.parse import quote_plus

from .integration_metadata import IntegrationMetadata


def build_connection_string(integration_metadata: IntegrationMetadata) -> str:
    stype = integration_metadata.service_type.lower()
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
    if integration_metadata.auth_method == 'basic' and integration_metadata.username and integration_metadata.password:
        auth = f'{quote_plus(integration_metadata.username)}:{quote_plus(integration_metadata.password)}@'
    elif integration_metadata.auth_method == 'windows' and integration_metadata.username and integration_metadata.windows_domain:
        domain_user = f'{integration_metadata.windows_domain}\\{integration_metadata.username}'
        auth = f'{quote_plus(domain_user)}:{quote_plus(integration_metadata.password or '')}@'
    elif integration_metadata.auth_method == 'kerberos':
        auth = ''
    else:
        auth = ''

    host = integration_metadata.host
    port = integration_metadata.port
    db = integration_metadata.database_name or ''

    query = ''
    if integration_metadata.extra_options:
        query = '&'.join(
            f'{quote_plus(str(k))}={quote_plus(str(v))}'
            for k, v in integration_metadata.extra_options.items()
        )
        query = f'?{query}'

    if stype == 'snowflake':
        account = host
        schema = integration_metadata.extra_options.get('schema', '') if integration_metadata.extra_options else ''
        db_path = f'/{db}/{schema}' if schema else f'/{db}'
        return f'{scheme}://{auth}{account}{db_path}{query}'

    if stype == 'sqlserver':
        query = query or '?driver=ODBC+Driver+17+for+SQL+Server'

    return f'{scheme}://{auth}{host}:{port}/{db}{query}'