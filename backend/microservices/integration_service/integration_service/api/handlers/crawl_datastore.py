from uuid import UUID

from kafka_messaging.events.integration_service import (
    DataStoreCreated,
    DataStoreMetaCrawled,
    TableMeta,
)
from kafka_messaging.message_bus import get_kafka_message_bus
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from svc_integration_contracts.models import CrawlResponse, FilteredCrawlRequest

from integration_service.database.repositories import DataStoreRepository
from integration_service.services.crawl.catalog_builder.build_datastores_registry_catalog import (
    build_datastores_registry_catalog,
)
from integration_service.services.crawl.filters.factory import create_specs
from integration_service.services.crawl.filters.logic import AlwaysTrueSpec


async def crawl_initial_datastore_metadata(
    event: DataStoreCreated, repo: DataStoreRepository, engine_manager: EngineManager
) -> None:
    datastore_registry = await build_datastores_registry_catalog(
        repo=repo,
        engine_manager=engine_manager,
        user_id=event.user_id,
        organization_id=event.organization_id,
        datastore_ids=[event.datastore_id],
        datastore_spec=AlwaysTrueSpec(),
        schema_spec=AlwaysTrueSpec(),
        table_spec=AlwaysTrueSpec(),
    )
    await get_kafka_message_bus().publish(
        DataStoreMetaCrawled(
            user_id=event.user_id,
            organization_id=event.organization_id,
            table_metas=[
                TableMeta(
                    datastore_id=table_meta.get("datastore_id"),
                    datastore_name=event.datastore_name,
                    datastore_descr=event.datastore_descr,
                    schema_name=table_meta.get("schema_name"),
                    table_name=table_meta.get("table_name"),
                    column_names=table_meta.get("column_names"),
                )
                for table_meta in datastore_registry.table_metas
            ],
        )
    )


async def crawl_filtered_datastore_metadata(
    user_id: UUID,
    organization_id: UUID,
    inspection_request: FilteredCrawlRequest,
    repo: DataStoreRepository,
    engine_manager: EngineManager,
) -> CrawlResponse:
    datastore_spec, schema_spec, table_spec = create_specs(
        datastores=inspection_request.datastores,
        schemas=inspection_request.schemas,
        tables=inspection_request.tables,
    )

    datastore_registry = await build_datastores_registry_catalog(
        repo=repo,
        engine_manager=engine_manager,
        user_id=user_id,
        organization_id=organization_id,
        datastore_ids=inspection_request.datastores,
        datastore_spec=datastore_spec,
        schema_spec=schema_spec,
        table_spec=table_spec,
    )

    return CrawlResponse(
        datastore_registry_repr=repr(datastore_registry),
        datastores_enum=datastore_registry.datastores_enum,
        schemas_enum=datastore_registry.schemas_enum,
        tables_enum=datastore_registry.tables_enum,
        columns_enum=datastore_registry.columns_enum,
        filter_op_enum=datastore_registry.filter_op_enum,
        agg_funcs_enum=datastore_registry.agg_funcs_enum,
    )
