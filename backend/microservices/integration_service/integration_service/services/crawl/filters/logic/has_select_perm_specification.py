import logging
from typing import Set
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import text

from integration_service.services.crawl.filters.logic import Specification

logger = logging.getLogger(__name__)


SELECT_PERM_STMT = {
    'mssql': '''
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = :schema
        AND HAS_PERMS_BY_NAME(
            QUOTENAME(TABLE_SCHEMA) + '.' + QUOTENAME(TABLE_NAME),
            'OBJECT', 'SELECT'
        ) = 1
    ''',
    'postgresql': '''
        SELECT table_name FROM INFORMATION_SCHEMA.TABLES
        WHERE   table_schema = :schema
                AND has_table_privilege(current_user, table_schema || '.' || table_name, 'SELECT')
    ''',
    'mysql': '''
        SELECT DISTINCT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLE_PRIVILEGES
        WHERE TABLE_SCHEMA = :schema
        AND PRIVILEGE_TYPE = 'SELECT'
        UNION
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = :schema
        AND EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.SCHEMA_PRIVILEGES
            WHERE TABLE_SCHEMA = :schema
            AND PRIVILEGE_TYPE = 'SELECT'
        )
        UNION
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = :schema
        AND EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.USER_PRIVILEGES
            WHERE PRIVILEGE_TYPE = 'SELECT'
        )
    '''
}


class HasSelectPermissionSpec(Specification):
    def __init__(self, crawler: Inspector, schema_name: str):
        self._accessible = self._fetch_accessible(crawler, schema_name)

    def is_satisfied_by(self, candidate) -> bool:
        if self._accessible is None:
            return True
        return candidate.name in self._accessible

    def is_empty(self):
        return self._accessible is not None and len(self._accessible) == 0

    def _fetch_accessible(self, crawler: Inspector, schema_name: str) -> Set[str] | None:
        dialect = crawler.dialect.name
        logger.info('Fetching accessible permissions for schema %s, dialog: %s', schema_name, dialect)
        try:
            conn = crawler.bind
            if (stmt := SELECT_PERM_STMT.get(dialect)) is not None:
                result = conn.execute(text(stmt), {'schema': schema_name})
                logger.info('Allowed schemas: %s', result)
                return {row[0] for row in result}
            elif dialect == 'snowflake':
                return self._probe_snowflake(conn, schema_name, crawler)
            else:
                return None
        except Exception as e:
            logger.warning(f'Permission filter failed for {schema_name}: {e}')
            return None

    def _probe_snowflake(self, conn, schema_name: str, crawler: Inspector) -> Set[str]:
        accessible = set()
        try:
            table_names = crawler.get_table_names(schema=schema_name)
        except Exception as e:
            logger.warning(f'Snowflake table listing failed for {schema_name}: {e}')
            return accessible

        for table_name in table_names:
            try:
                conn.execute(text(
                    f'SELECT 1 FROM "{schema_name}"."{table_name}" LIMIT 1'
                ))
                accessible.add(table_name)
            except Exception:
                logger.debug(f'No SELECT access on {schema_name}.{table_name}, skipping')
        return accessible
