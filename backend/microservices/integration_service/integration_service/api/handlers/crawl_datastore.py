from uuid import UUID
from svc_integration_contracts.models import FilteredCrawlRequest, CrawlResponse
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from kafka_messaging.message_bus import get_kafka_message_bus
from kafka_messaging.events.integration_service import IntegrationMetaCrawled, TableMeta, IntegrationCreated

from integration_service.database.repositories import DataStoreRepository
from integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog import build_integrations_registry_catalog
from integration_service.services.crawl.filters.logic import AlwaysTrueSpec
from integration_service.services.crawl.filters.factory import create_specs


async def crawl_initial_integration_metadata(
    event: IntegrationCreated,
    repo: DataStoreRepository,
    engine_manager: EngineManager
) -> None:
    integration_registry = await build_integrations_registry_catalog(
        repo=repo,
        engine_manager=engine_manager,
        user_id=event.user_id,
        organization_id=event.organization_id,
        integration_ids=[event.integration_id],
        integration_spec=AlwaysTrueSpec(),
        schema_spec=AlwaysTrueSpec(),
        table_spec=AlwaysTrueSpec()
    )
    await get_kafka_message_bus().publish(
        IntegrationMetaCrawled(
            user_id=event.user_id,
            organization_id=event.organization_id,
            table_metas=[TableMeta(
                integration_id=table_meta.get('integration_id'),
                integration_name=event.integration_name,
                integration_descr=event.integration_descr,
                schema_name=table_meta.get('schema_name'),
                table_name=table_meta.get('table_name'),
                column_names=table_meta.get('column_names'),
            ) for table_meta in integration_registry.table_metas]
        )
    )


async def crawl_filtered_integration_metadata(
        user_id: UUID,
        organization_id: UUID,
        inspection_request: FilteredCrawlRequest,
        repo: DataStoreRepository,
        engine_manager: EngineManager
) -> CrawlResponse:
    integration_spec, schema_spec, table_spec = create_specs(
        integrations=inspection_request.integrations,
        schemas=inspection_request.schemas,
        tables=inspection_request.tables
    )

    integration_registry = await build_integrations_registry_catalog(
        repo=repo,
        engine_manager=engine_manager,
        user_id=user_id,
        organization_id=organization_id,
        integration_ids=inspection_request.integrations,
        integration_spec=integration_spec,
        schema_spec=schema_spec,
        table_spec=table_spec
    )

    return CrawlResponse(
        integration_registry_repr=repr(integration_registry),
        integrations_enum=integration_registry.integrations_enum,
        schemas_enum=integration_registry.schemas_enum,
        tables_enum=integration_registry.tables_enum,
        columns_enum=integration_registry.columns_enum,
        filter_op_enum=integration_registry.filter_op_enum,
        agg_funcs_enum=integration_registry.agg_funcs_enum
    )
