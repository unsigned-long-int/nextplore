import asyncio

from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from nextplore_sdk.database.connection_maker.mappers.to_domain_auth import (
    to_domain_auth,
)
from nextplore_sdk.database.connection_maker.mappers.to_domain_cloud import (
    to_domain_cloud,
)
from nextplore_sdk.database.connection_maker.mappers.to_domain_db import to_domain_db
from nextplore_sdk.database.connection_maker.models.connection_profile import (
    ConnectionProfile,
)
from sqlalchemy import Select
from svc_llm_inference_contracts.models import ORMContextResponse

from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.api.models.ai_query_response import AIQueryResponse
from nextplore_orchestrator.clients.integration import IntegrationClient
from nextplore_orchestrator.domain.models import ORMRequest, StatementRequest

from .orm_factory import get_orm
from .run_query import run_query
from .statement_factory import get_statement


class QueryExecutor:
    def __init__(
        self,
        integration_client: IntegrationClient,
        engine_manager: EngineManager,
    ) -> None:
        self.integration_client = integration_client
        self.engine_manager = engine_manager

    async def execute(
        self, orm_context: ORMContextResponse, user_identity: UserIdentity
    ) -> AIQueryResponse:
        connection_profile = await self._get_connection_profile(
            orm_context, user_identity
        )
        stmt = await self._build_statement(orm_context, connection_profile)
        engine = await self.engine_manager.acquire_engine(connection_profile)
        return await asyncio.to_thread(run_query, stmt, engine)

    async def _get_connection_profile(
        self, orm_context: ORMContextResponse, user_identity: UserIdentity
    ) -> ConnectionProfile:
        connection_profile = (
            await self.integration_client.get_datastore_connection_profile(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                datastore_id=orm_context.datastore,
            )
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
            region=connection_profile.region,
        )

    async def _build_statement(
        self, orm_context: ORMContextResponse, connection_profile: ConnectionProfile
    ) -> Select:
        orm_request = ORMRequest(
            datastore=orm_context.datastore,
            schema_name=orm_context.schema_name,
            class_name=orm_context.class_name,
            table_name=orm_context.table_name,
        )
        orm = await get_orm(
            orm_request=orm_request,
            connection_profile=connection_profile,
            engine_manager=self.engine_manager,
        )
        statement_request = StatementRequest(
            orm_model=orm,
            datastore=orm_context.datastore,
            column_names=orm_context.column_names,
            column_aggregates=orm_context.column_aggregates,
            column_filters=orm_context.column_filters,
        )
        stmt = get_statement(statement_request)
        return stmt
