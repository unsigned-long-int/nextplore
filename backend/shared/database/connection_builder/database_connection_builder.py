from urllib.parse import quote_plus
from .connection_meta import ConnectionMeta


def build_connection_string(connection_meta: ConnectionMeta) -> str:
    stype = connection_meta.service_type.lower()
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
    if connection_meta.auth_method == 'basic' and connection_meta.username and connection_meta.password:
        auth = f'{quote_plus(connection_meta.username)}:{quote_plus(connection_meta.password)}@'
    elif connection_meta.auth_method == 'windows' and connection_meta.username and connection_meta.windows_domain:
        domain_user = f'{connection_meta.windows_domain}\\{connection_meta.username}'
        auth = f'{quote_plus(domain_user)}:{quote_plus(connection_meta.password or "")}@'
    elif connection_meta.auth_method == 'kerberos':
        auth = ''
    else:
        auth = ''

    host = connection_meta.host
    port = connection_meta.port
    db = connection_meta.database_name or ''

    query = ''
    if connection_meta.extra_options:
        query = '&'.join(
            f'{quote_plus(str(k))}={quote_plus(str(v))}'
            for k, v in connection_meta.extra_options.items()
        )
        query = f'?{query}'

    if stype == 'snowflake':
        account = host
        schema = connection_meta.extra_options.get('schema', '') if connection_meta.extra_options else ''
        db_path = f'/{db}/{schema}' if schema else f'/{db}'
        return f'{scheme}://{auth}{account}{db_path}{query}'

    if stype == 'sqlserver':
        query = query or '?driver=ODBC+Driver+18+for+SQL+Server'

    return f'{scheme}://{auth}{host}:{port}/{db}{query}'