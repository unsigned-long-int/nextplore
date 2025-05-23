from sqlalchemy import inspect, Engine, Inspector, quoted_name
from typing import Dict, List, Optional
from functools import partial

from infrastructure.event_orchestration_service.event_orchestrator import EventOrchestrator
from infrastructure.event_orchestration_service.events import events

from .database_descriptor import DatabaseDescriptor
from .schema_descriptor import SchemaDescriptor
from .table_descriptor import TableDescriptor
from .database_inspection_filter import DatabaseInspectionFilter
from .table_inspection_service import (
    TableDescriptorGeneratorError,
    fetch_table
)


def fetch_database_descriptor(
        event_orchestrator: EventOrchestrator,
        engine: Engine,
        database_inspection_filters: Optional[List[DatabaseInspectionFilter]] = None
) -> DatabaseDescriptor:
    inspector = inspect(engine)
    if database_inspection_filters is None:
        return fetch_all(
            event_orchestrator=event_orchestrator,
            inspector=inspector
        )

    return fetch_filtered(
        event_orchestrator=event_orchestrator,
        inspector=inspector,
        database_inspection_filters=database_inspection_filters
    )


def fetch_all(
        event_orchestrator: EventOrchestrator,
        inspector: Inspector
) -> DatabaseDescriptor:
    schema_names = inspector.get_schema_names()
    schemas: Dict[str, SchemaDescriptor] = {}

    for schema_name in schema_names:
        tables: Dict[str, TableDescriptor] = {}

        table_names = inspector.get_table_names(
            schema=quoted_name(schema_name, True)
            )
        for table_name in table_names:
            try:
                table: Dict[str, TableDescriptor] = fetch_table(
                    inspector=inspector,
                    schema_name=quoted_name(schema_name, True),
                    table_name=table_name
                )
                tables.update(table)
            except TableDescriptorGeneratorError as e:
                event = events.TableDescriptorGenerationFailed(str(e))
                event_orchestrator.queue.append(event)

        schemas.update({schema_name: SchemaDescriptor(tables)})
    return DatabaseDescriptor(
        schemas=schemas,
        event_orchestrator=event_orchestrator
    )


def fetch_filtered(
        event_orchestrator: EventOrchestrator,
        inspector: Inspector,
        database_inspection_filters: List[DatabaseInspectionFilter]
) -> DatabaseDescriptor:
    schemas: Dict[str, SchemaDescriptor] = {}
    for db_inspection_filter in database_inspection_filters:
        try:
            table: Dict[str, TableDescriptor] = fetch_table(
                inspector=inspector,
                schema_name=db_inspection_filter.schema_name,
                table_name=db_inspection_filter.table_name
            )
            schema = schemas.get(
                db_inspection_filter.schema_name,
                SchemaDescriptor()
            )

            schema.tables.update(table)

            schemas.update({
                db_inspection_filter.schema_name: schema
            })
        except TableDescriptorGeneratorError as e:
            event = events.TableDescriptorGenerationFailed(str(e))
            event_orchestrator.queue.append(event)
    return DatabaseDescriptor(
        schemas=schemas,
        event_orchestrator=event_orchestrator
    )
