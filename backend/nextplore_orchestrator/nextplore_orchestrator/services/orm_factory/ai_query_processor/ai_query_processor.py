import logging
import asyncio
from typing import List
from uuid import UUID
from sqlalchemy import Select

from nextplore_orchestrator.clients.embedding import EmbeddingClient
from nextplore_orchestrator.clients.vector import VectorClient
from nextplore_orchestrator.clients.integration import IntegrationClient
from nextplore_orchestrator.clients.llm_inference import LlmInferenceClient
from nextplore_orchestrator.services.orm_factory.orm import get_orm
from nextplore_orchestrator.domain.models import ORMRequest, StatementRequest
from nextplore_orchestrator.services.orm_factory.statement import get_statement
from nextplore_orchestrator.services.rag import build_rag_context, RAGContext
from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.clients.embedding.models.embedding_response import EmbeddingResponse
from nextplore_orchestrator.clients.llm_inference.models.orm_context_request import ORMContextRequest, Context
from nextplore_orchestrator.clients.llm_inference.models.orm_context_response import ORMContextResponse
from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest
from nextplore_orchestrator.api.models.ai_query_response import AIQueryResponse
from nextplore_orchestrator.clients.vector.models.qdrant_vector_response import QDrantVectorResponse
from nextplore_orchestrator.clients.vector.models.qdrant_vector_request import QDrantVectorRequest
from nextplore_orchestrator.clients.vector.models.vector_meta_request import VectorMetaRequest
from nextplore_orchestrator.clients.vector.models.vector_meta_response import VectorMetaResponse
from nextplore_orchestrator.services.orm_factory.ai_query_processor.run_query import run_query
from nextplore_sdk.database.connection_maker.models.connection_profile import ConnectionProfile
from nextplore_sdk.database.connection_maker.mappers.to_domain_db import to_domain_db
from nextplore_sdk.database.connection_maker.mappers.to_domain_auth import to_domain_auth
from nextplore_sdk.database.connection_maker.mappers.to_domain_cloud import to_domain_cloud
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager


logger = logging.getLogger(__name__)


class AIQueryProcessor:
    def __init__(
        self,
        embedding_client: EmbeddingClient,
        vector_client: VectorClient,
        integration_client: IntegrationClient,
        llm_inference_client: LlmInferenceClient,
        user_identity: UserIdentity,
        engine_manager: EngineManager
    ) -> None:
        self.embedding_client = embedding_client
        self.vector_client = vector_client
        self.integration_client = integration_client
        self.llm_inference_client = llm_inference_client
        self.user_identity = user_identity
        self.engine_manager = engine_manager

    async def run(self, request: AIQueryRequest) -> AIQueryResponse:
        query_vector_response = await self._embed_prompt(request.prompt)
        nearest_vectors = await self._get_nearest_neighbours(query_vector_response.embedding)
        vectors_meta = await self._get_nearest_vector_metas(nearest_vectors.vector_ids)
        rag_context = build_rag_context(vectors_meta)
        orm_context = await self._get_ai_orm_context(request, rag_context)
        ai_query_response = await self._build_ai_query_response(orm_context)
        return ai_query_response

    async def _embed_prompt(self, datastream: str) -> EmbeddingResponse:
        return await self.embedding_client.embed(datastream)
    
    async def _get_nearest_neighbours(self, embedding: List[float]) -> QDrantVectorResponse:
        payload = QDrantVectorRequest(embedding=embedding)
        return await self.vector_client.get_nearest_neighbours(
            organization_id=self.user_identity.organization_id,
            user_id=self.user_identity.user_id,
            payload=payload
        )
    
    async def _get_nearest_vector_metas(self, vector_ids: List[UUID]) -> List[VectorMetaResponse]:
        payload = VectorMetaRequest(
            vector_ids=vector_ids
        )
        return await self.vector_client.get_meta(
            organization_id=self.user_identity.organization_id,
            user_id=self.user_identity.user_id,
            payload=payload
        )
    
    async def _get_ai_orm_context(self, request: AIQueryRequest, rag_context: RAGContext) -> ORMContextResponse:
        context = Context(**rag_context.model_dump())
        orm_context_request = ORMContextRequest(
            provider=request.provider,
            model_id=request.model_id,
            query=request.prompt,
            context=context
        )
        return await self.llm_inference_client.get_orm_context(
            organization_id=self.user_identity.organization_id,
            user_id=self.user_identity.user_id,
            payload=orm_context_request
        )
    
    async def _get_connection_profile(self, orm_context: ORMContextResponse) -> ConnectionProfile:
        connection_profile = await self.integration_client.get_connection_profile(
            organization_id=self.user_identity.organization_id,
            user_id=self.user_identity.user_id,
            integration_id=orm_context.integration
        )
        return ConnectionProfile(
            cloud=to_domain_cloud(connection_profile.cloud.value),
            auth=to_domain_auth(connection_profile.auth.value),
            db=to_domain_db(connection_profile.db.value),
            host=connection_profile.host,
            database=connection_profile.database_name,
            port=connection_profile.port,
            warehouse=connection_profile.warehouse,
            username=connection_profile.username,
            password=connection_profile.password,
            client_secret=connection_profile.client_secret,
            aws_external_id=connection_profile.aws_external_id,
            aws_role_arn=connection_profile.aws_role_arn,
            snowflake_private_key=connection_profile.snowflake_private_key,
            azure_cert_kid=connection_profile.azure_cert_kid,
            tenant_id=connection_profile.tenant_id,
            client_id=connection_profile.client_id,
            region=connection_profile.region
        )

    async def _build_statement(self, orm_context: ORMContextResponse, connection_profile: ConnectionProfile) -> Select:
        orm_request = ORMRequest(
            integration=orm_context.integration,
            schema_name=orm_context.schema_name,
            class_name=orm_context.class_name,
            table_name=orm_context.table_name
        )
        orm = await get_orm(
            orm_request=orm_request,
            connection_profile=connection_profile,
            engine_manager=self.engine_manager
        )
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
        connection_profile = await self._get_connection_profile(orm_context)
        stmt = await self._build_statement(
            orm_context=orm_context, 
            connection_profile=connection_profile
        )
        engine = await self.engine_manager.acquire_engine(connection_profile)
        return await asyncio.to_thread(
            run_query,
            stmt,
            engine
        )
