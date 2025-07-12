from uuid import UUID
from sqlalchemy import inspect
from sqlalchemy.engine.reflection import Inspector

from shared.database.models import IntegrationORM
from shared.database.dependencies import backend_session_scope
from shared.database.connection_builder import build_connection_string, create_integration_metadata
from shared.database.sql_connection_service import fetch_engine


class IntegrationNotFoundError(Exception):
    pass


def get_crawler(integration_id: UUID) -> Inspector:
    with backend_session_scope() as scoped_session:
        integration_orm = (
            scoped_session.query(IntegrationORM)
            .filter_by(id=integration_id)
            .first()
        )
        if not integration_orm:
            raise IntegrationNotFoundError(f'Integration with id {integration_id} not found.')
        
        integration_metadata = create_integration_metadata(integration_orm)

    sql_connection_string = build_connection_string(integration_metadata)
    engine = fetch_engine(sql_connection_string)
    inspector = inspect(engine)
    return inspector
