from fastapi import APIRouter, Depends
from api.models import AIQueryRequest, AIQueryResponse
from core.orm_factory import AIORMFactory
from sqlalchemy import select
from sqlalchemy.orm import aliased

from services.credentials_loader import load_credentials
from services.authentication import get_active_user
from services.open_ai_client_loader import load_open_ai_client
from services.sql_connection_service import fetch_engine, fetch_session_maker, session_scope
from services.identity_service import resolve_user_identity
from services.database.repositories import IntegrationRepository, VectorRepository
from core.orm_factory import generate_orm_statement


credentials = load_credentials()

client = load_open_ai_client(credentials.openai_api_key)
engine = fetch_engine(credentials.sql_connection_string)


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

    ai_orm_factory = AIORMFactory(
        client=client, 
        vectors_meta=vectors_meta
    )

    orm_request = ai_orm_factory.retrieve_orm_request(request.prompt)
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
    