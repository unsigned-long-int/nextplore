import os
from fastapi import APIRouter, Depends
from api.models import AIQueryRequest, AIQueryResponse

from internal_services.authentication import get_active_user
from internal_services.orm_factory import generate_orm_statement, AIORMRequestFactory
from shared.identity_service import resolve_user_identity
from shared.database.connection_builder import build_connection_string
from shared.database.sql_connection_service import fetch_engine, fetch_session_maker, session_scope
from shared.database.repositories import IntegrationRepository, VectorRepository
from shared.open_ai_client_loader import load_open_ai_client


client = load_open_ai_client(os.getenv('OPENAI_API_KEY'))
engine = fetch_engine(f'postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}')


router = APIRouter()

@router.post('', response_model=AIQueryResponse)
def ai_query(request: AIQueryRequest, user=Depends(get_active_user)) -> AIQueryResponse:
    azure_user_id = user.get('oid')
    azure_tenant_id = user.get('tid')

    user_identity = resolve_user_identity(azure_tenant_id, azure_user_id)
    integration_repo = IntegrationRepository()
    vector_repo = VectorRepository()

    integration_id_filter = [request.integration_id]

    if not request.integration_id:
        integration_id_filter = integration_repo.get_user_integration_ids(user_identity)
    
    if not integration_id_filter:
        vectors_meta = []
    else:
        vectors_meta = vector_repo.get_integration_vectors(integration_id_filter)

    ai_orm_factory = AIORMRequestFactory(
        client=client, 
        vectors_meta=vectors_meta
    )

    orm_request = ai_orm_factory.retrieve_orm_request(request.prompt)
    integration_metadata = integration_repo.get_integration_metadata(
        user_identity=user_identity,
        integration_id=orm_request.integration_id
    )
    engine = fetch_engine(sql_connection_string=build_connection_string(integration_metadata))
    session_factory = fetch_session_maker(engine)

    with session_scope(session_factory) as session:
        statement = generate_orm_statement(orm_request)
        query_result = session.execute(statement)
        headers = query_result.keys()
        sample = query_result.fetchall()
        if sample:
            return AIQueryResponse(
                sql=str(statement),
                data=[{column: str(getattr(row, column))
                       for column in headers} for row in sample]
            )
        return AIQueryResponse(
            sql=str(statement),
            data=[]
        )
    