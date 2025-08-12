from urllib.parse import quote_plus
from .scheme_factory import dispatch_scheme
from .connection_meta import ConnectionMeta


def build_connection_string(connection_meta: ConnectionMeta) -> str:
    stype = connection_meta.service_type.lower()

    scheme = dispatch_scheme(stype)

    auth = ''
    if connection_meta.auth_method == 'basic' and connection_meta.username and connection_meta.password:
        auth = f'{quote_plus(connection_meta.username)}:{quote_plus(connection_meta.password)}@'

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