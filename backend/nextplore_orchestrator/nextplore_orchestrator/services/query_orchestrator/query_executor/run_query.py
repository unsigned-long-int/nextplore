import logging
from sqlalchemy import Select, Engine
from sqlalchemy.exc import SQLAlchemyError

from nextplore_sdk.database.connection_maker.session.session_maker import fetch_session_maker, session_scope
from nextplore_orchestrator.api.models.ai_query_response import AIQueryResponse
from nextplore_orchestrator.services.query_orchestrator.exceptions import QueryRunError


logger = logging.getLogger(__name__)


def run_query(stmt: Select, engine: Engine):
    try:
        session_factory = fetch_session_maker(engine)
        with session_scope(session_factory) as session:
            query_result = session.execute(stmt)
            headers = query_result.keys()
            sample = query_result.fetchall()
            if sample:
                return AIQueryResponse(
                    sql=str(stmt),
                    data=[{column: str(getattr(row, column)) for column in headers} for row in sample]
                )
            return AIQueryResponse(
                sql=str(stmt),
                data=[]
            )
    except SQLAlchemyError as e:
        logger.error(f'Query failed with error code: {str(e)}')
        raise QueryRunError('Query run failed with database error') from e
