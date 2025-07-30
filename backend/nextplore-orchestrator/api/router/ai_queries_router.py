import os
from fastapi import APIRouter, Depends
from api.models import AIQueryRequest, AIQueryResponse

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import (
    get_integration_client, 
    get_vector_client,
    get_embedding_client
)
from internal_services.orm_factory import generate_orm_statement, AIORMRequestFactory
from shared.contracts.integration_service import IntegrationMetadataRequest
from shared.database.connection_builder import build_connection_string, ConnectionMeta
from shared.database.sql_connection_service import fetch_engine, fetch_session_maker, session_scope
from shared.open_ai_client_loader import load_open_ai_client


client = load_open_ai_client(os.getenv('OPENAI_API_KEY'))


router = APIRouter()

@router.post('', response_model=AIQueryResponse)
async def ai_query(
    request: AIQueryRequest, 
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client),
    vector_client=Depends(get_vector_client),
    embedding_client=Depends(get_embedding_client)
) -> AIQueryResponse:
    
    ai_orm_factory = AIORMRequestFactory(
        client=client, 
        user_identity=user_identity,
        vector_client=vector_client,
        integration_client=integration_client,
        embedding_client=embedding_client
    )

    orm_request = await ai_orm_factory.retrieve_orm_request(request.prompt)
    payload = IntegrationMetadataRequest(
        integration_id=orm_request.integration_id,
        user_id=user_identity.user_id,
        organization_id=user_identity.organization_id
    )
    integration = await integration_client.get_integration(payload)
    connection_meta = ConnectionMeta(
        service_type=integration.service_type,
        auth_method=integration.auth_method,
        host=integration.host,
        port=integration.port,
        database_name=integration.database_name,
        username=integration.username,
        password=integration.password,
        kerberos_principal=integration.kerberos_principal,
        windows_domain=integration.windows_domain,
        extra_options=integration.extra_options
    )
    engine = fetch_engine(sql_connection_string=build_connection_string(connection_meta))
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
    