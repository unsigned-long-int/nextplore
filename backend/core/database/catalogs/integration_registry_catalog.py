from dataclasses import dataclass, field 
from typing import Tuple, List, Dict, ClassVar
from uuid import UUID

from .integration_catalog import IntegrationCatalog

@dataclass(frozen=True)
class IntegrationRegistryCatalog:
    filter_op_enum: ClassVar[List[str]] = ['==', '!=', '>', '<', '>=', '<=', 'like', 'not like', 'in']
    agg_funcs_enum: ClassVar[List[str]] = ['sum', 'avg', 'min', 'max', 'count']

    integrations: Tuple[IntegrationCatalog] = field(default_factory=tuple)


    def fetch_first_matched_metadata(self) -> Dict[str, str]:
        if not self.integrations:
            return {'integration_id': None, 'schema_name': None, 'table_name': None}

        integration = self.integrations[0]
        schema = next(iter(integration.schemas), None)
        table = next(iter(schema.tables), None) if schema else None

        print(table)
        return {
            'integration_id': integration.id,
            'schema_name': schema.name if schema else None,
            'table_name': table.name if table else None,
            'reflected_columns': table.columns if table else None
        }

    @property
    def integrations_enum(self) -> List[UUID]:
        return [str(integration.id) for integration in self.integrations]
    
    @property
    def table_metas(self) -> List[Dict[str, str | List[str]]]:
        return [
            {'integration_id': integration.id,
             'schema_name': schema.name,
             'table_name': table.name,
             'column_names': table.column_names}
             for integration in self.integrations
             for schema in integration.schemas
             for table in schema.tables
        ]

    @property
    def schemas_enum(self) -> List[str]:
        return [
            schema.name
            for integration in self.integrations
            for schema in integration.schemas
        ]
    
    @property
    def tables_enum(self) -> List[str]:
        return [
            table.name
            for integration in self.integrations
            for schema in integration.schemas
            for table in schema.tables
        ]
    
    @property
    def columns_enum(self) -> List[str]:
        return [
            column
            for integration in self.integrations
            for schema in integration.schemas
            for table in schema.tables
            for column in table.column_names
        ]
    
    def __repr__(self) -> str:
        descriptor: List[str] = [
            f'integration_id={integration.id}: [{repr(integration)}]'
            for integration in self.integrations
        ]
        return ' | '.join(descriptor)
    