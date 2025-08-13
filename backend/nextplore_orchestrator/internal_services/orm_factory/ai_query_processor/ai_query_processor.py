import logging
from typing import List
from uuid import UUID
from sqlalchemy import Select

from clients.embedding import EmbeddingClient
from clients.vector import VectorClient
from clients.integration import IntegrationClient
from clients.ai_orm_context import AIORMContextClient
from internal_services.orm_factory.orm import get_orm, ORMRequest
from internal_services.orm_factory.statement import get_statement, StatementRequest
from internal_services.context import build_rag_context, RAGContext
from api.context import UserIdentity
from nextplore_sdk.database.sql_connection_service.session_starter import fetch_engine, fetch_session_maker, session_scope
from nextplore_sdk.contracts.embedding_service.embedding_response import EmbeddingResponse
from nextplore_sdk.contracts.nextplore_orchestrator_service.ai_query_request import AIQueryRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.ai_query_response import AIQueryResponse
from nextplore_sdk.contracts.vector_service.qdrant_vector_response import QDrantVectorResponse
from nextplore_sdk.contracts.vector_service.qdrant_vector_request import QDrantVectorRequest 
from nextplore_sdk.contracts.vector_service.vector_meta_request import VectorMetaRequest
from nextplore_sdk.contracts.vector_service.vector_meta_response import VectorMetaResponse
from nextplore_sdk.contracts.integration_service.integration_metadata_request import IntegrationMetadataRequest
from nextplore_sdk.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest, Context
from nextplore_sdk.contracts.ai_orm_context_service.orm_context_response import ORMContextResponse
from nextplore_sdk.database.connection_builder.database_connection_builder import build_connection_string, ConnectionMeta


logger = logging.getLogger(__name__)


class AIQueryProcessor:
    def __init__(
            self,
            embedding_client: EmbeddingClient,
            vector_client: VectorClient,
            integration_client: IntegrationClient,
            ai_orm_context_client: AIORMContextClient,
            user_identity: UserIdentity
    ) -> None:
        self.embedding_client = embedding_client
        self.vector_client = vector_client
        self.integration_client = integration_client
        self.ai_orm_context_client = ai_orm_context_client
        self.user_identity = user_identity

    async def run(self, request: AIQueryRequest) -> AIQueryResponse:
        query_vector_response = await self._embed_prompt(request.prompt)
        nearest_vectors = await self._get_nearest_vectors(query_vector_response.embedding)
        vectors_meta = await self._get_nearest_vector_metas(nearest_vectors.vector_ids)
        rag_context = build_rag_context(vectors_meta)
        orm_context = await self._get_ai_orm_context(request, rag_context)
        ai_query_response = await self._build_ai_query_response(orm_context)
        return ai_query_response

    async def _embed_prompt(self, datastream: str) -> EmbeddingResponse:
        return await self.embedding_client.embed(datastream)
    
    async def _get_nearest_vectors(self, embedding: List[float]) -> QDrantVectorResponse:
        payload = QDrantVectorRequest(embedding=embedding)
        return await self.vector_client.get_nearest_qdrant_vectors(payload)
    
    async def _get_nearest_vector_metas(self, vector_ids: List[UUID]) -> List[VectorMetaResponse]:
        payload = VectorMetaRequest(
            vector_ids=vector_ids
        )
        return await self.vector_client.get_vector_metas(payload)
    
    async def _get_ai_orm_context(self, request: AIQueryRequest, rag_context: RAGContext) -> ORMContextResponse:
        context = Context(**rag_context.model_dump())
        orm_context_request = ORMContextRequest(
            provider=request.provider,
            model_id=request.model_id,
            query=request.prompt,
            context=context
        )
        return await self.ai_orm_context_client.get_orm_context(orm_context_request)
    
    async def _get_connection_string(self, orm_context: ORMContextResponse) -> str:
        payload = IntegrationMetadataRequest(
            integration_id=orm_context.integration,
            user_id=self.user_identity.user_id,
            organization_id=self.user_identity.organization_id
        )
        integration = await self.integration_client.get_integration(payload)
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
        connection_string = build_connection_string(connection_meta)
        return connection_string

    def _build_statement(self, orm_context: ORMContextResponse, connection_string: str) -> Select:
        orm_request = ORMRequest(
            integration=orm_context.integration,
            schema_name=orm_context.schema_name,
            class_name=orm_context.class_name,
            table_name=orm_context.table_name,
            connection_string=connection_string
        )
        orm = get_orm(orm_request)
        statement_request = StatementRequest(
            orm_model=orm,
            integration=orm_context.integration,
            column_names=orm_context.column_names,
            column_aggregates=orm_context.column_aggregates,
            column_filters=orm_context.column_filters
        )
        stmt = get_statement(statement_request)
        return stmt 

    async def _build_ai_query_response(self, orm_context: ORMContextResponse) -> AIQueryResponse:
        connection_string = await self._get_connection_string(orm_context)
        stmt = self._build_statement(orm_context, connection_string)
        engine = fetch_engine(sql_connection_string=connection_string)
        session_factory = fetch_session_maker(engine)

        with session_scope(session_factory) as session:
            query_result = session.execute(stmt)
            headers = query_result.keys()
            sample = query_result.fetchall()
            if sample:
                return AIQueryResponse(
                    sql=str(stmt),
                    data=[{column: str(getattr(row, column))
                        for column in headers} for row in sample]
                )
            return AIQueryResponse(
                sql=str(stmt),
                data=[]
            )

