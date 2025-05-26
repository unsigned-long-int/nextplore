from dataclasses import dataclass
from typing import Dict, List, ClassVar, Optional
from sqlalchemy.engine.interfaces import ReflectedColumn

from services.event_orchestration_service.event_orchestrator import EventOrchestrator
from services.event_orchestration_service.events import events

from .database_inspection_filter import DatabaseInspectionFilter
from .schema_descriptor import SchemaDescriptor
from .table_descriptor import ReflectedColumnMissing


@dataclass(frozen=True)
class DatabaseDescriptor:
    filter_op_enum: ClassVar[List[str]] = ['==', '!=', '>', '<', '>=', '<=', 'like', 'not like', 'in']
    agg_funcs_enum: ClassVar[List[str]] = ['sum', 'avg', 'min', 'max', 'count']
    schemas: Dict[str, SchemaDescriptor]
    event_orchestrator: EventOrchestrator

    def fetch_reflected_columns(
            self,
            database_inspection_filter: DatabaseInspectionFilter
    ) -> Optional[List[ReflectedColumn]]:
        schema_name = database_inspection_filter.schema_name
        table_name = database_inspection_filter.table_name
        if (schema := self.schemas.get(schema_name)) is None:
            message = f'SchemaDescriptor does not exist for: {schema_name}'
            event = events.SchemaDescriptorNotFound(message)
            self.event_orchestrator.queue.append(event)
            return None

        if (table := schema.tables.get(table_name)) is None:
            message = f'TableDescriptor does not exist for {table_name}'
            event = events.TableDescriptorNotFound(message)
            self.event_orchestrator.queue.append(event)
            return None

        return table.columns

    @property
    def table_metas(self) -> List[Dict[str, str | List[str]]]:
        return [
            {'schema_name': schema_name,
             'table_name': table_name,
             'column_names': table.column_names}
            for schema_name, schema in self.schemas.items()
            for table_name, table in schema.tables.items()
        ]

    @property
    def schema_name_enum(self) -> List[str]:
        return list(self.schemas.keys())

    @property
    def table_name_enum(self) -> List[str]:
        return [
            table_name
            for _, schema in self.schemas.items()
            for table_name in schema.tables.keys()
        ]

    @property
    def column_names_enum(self) -> List[str]:
        return [
            column_name
            for schema in self.schemas.values()
            for table in schema.tables.values()
            for column_name in table.column_names
        ]

    def __repr__(self) -> str:
        descriptor: List[str] = [
            f'schema_name={schema_name}: [{repr(schema)}]'
            for schema_name, schema in self.schemas.items()
        ]
        return ' | '.join(descriptor)
