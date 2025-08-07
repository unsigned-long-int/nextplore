from nextplore_shared.contracts.integration_service.filtered_crawl_request import FilteredCrawlRequest
from nextplore_shared.contracts.integration_service.crawl_response import CrawlResponse
from services import crawl_integration_registry
from utils.filters.logic import AlwaysTrueSpec
from utils.filters.factory import create_specs
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationMetaCrawled, IntegrationCreated



async def crawl_initial_integration_metadata(event: IntegrationCreated) -> None:
    integration_registry = await crawl_integration_registry(
        integration_ids=[event.integration_id],
        integration_spec=AlwaysTrueSpec(),
        schema_spec = AlwaysTrueSpec(),
        table_spec=AlwaysTrueSpec()
    )
    print(f'metadata crawled: {integration_registry}')
    await get_kafka_message_bus().publish(
        IntegrationMetaCrawled(
            user_id=event.user_id,
            organization_id=event.organization_id,
            table_metas=integration_registry.table_metas
        )
    )


async def craw_filtered_integration_metadata(inspection_request: FilteredCrawlRequest) -> CrawlResponse:
    integration_spec, schema_spec, table_spec = create_specs(
        integrations=inspection_request.integrations,
        schemas=inspection_request.schemas,
        tables=inspection_request.tables
    )

    integration_registry = await crawl_integration_registry(
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
