from shared.contracts.integration_service import (
    InitialCrawlRequest, 
    FilteredCrawlRequest, 
    CrawlResponse
)
from services import crawl_integration_registry
from utils.filters.logic import AlwaysTrueSpec
from utils.filters.factory import create_specs
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationMetaCrawled



def crawl_initial_integration_metadata(inspection_request: InitialCrawlRequest) -> None:
    integration_registry = crawl_integration_registry(
        integration_ids=[inspection_request.integration_id],
        integration_spec=AlwaysTrueSpec(),
        schema_spec = AlwaysTrueSpec(),
        table_spec=AlwaysTrueSpec()
    )
    print(f'metadata crawled: {integration_registry}')
    get_kafka_message_bus().publish(IntegrationMetaCrawled(table_metas=integration_registry.table_metas))


def craw_filtered_integration_metadata(inspection_request: FilteredCrawlRequest) -> CrawlResponse:
    integration_spec, schema_spec, table_spec = create_specs(
        integrations=inspection_request.integrations,
        schemas=inspection_request.schemas,
        tables=inspection_request.tables
    )

    integration_registry = crawl_integration_registry(
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
