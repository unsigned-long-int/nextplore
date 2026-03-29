from dataclasses import dataclass, field 
from typing import Tuple, List, Dict, ClassVar
from uuid import UUID

from .datastore_catalog import DataStoreCatalog


@dataclass(frozen=True)
class DataStoreRegistryCatalog:
    filter_op_enum: ClassVar[List[str]] = ['==', '!=', '>', '<', '>=', '<=', 'like', 'not like', 'in']
    agg_funcs_enum: ClassVar[List[str]] = ['sum', 'avg', 'min', 'max', 'count']

    datastores: Tuple[DataStoreCatalog] = field(default_factory=tuple)

    @property
    def datastores_enum(self) -> List[str]:
        return [str(datastore.id) for datastore in self.datastores]
    
    @property
    def table_metas(self) -> List[Dict[str, UUID | str | List[str]]]:
        return [
            {
                'datastore_id': datastore.id,
                'schema_name': schema.name,
                'table_name': table.name,
                'column_names': table.column_names}
            for datastore in self.datastores
            for schema in datastore.schemas
            for table in schema.tables
        ]

    @property
    def schemas_enum(self) -> List[str]:
        return [
            schema.name
            for datastore in self.datastores
            for schema in datastore.schemas
        ]
    
    @property
    def tables_enum(self) -> List[str]:
        return [
            table.name
            for datastore in self.datastores
            for schema in datastore.schemas
            for table in schema.tables
        ]
    
    @property
    def columns_enum(self) -> List[str]:
        return [
            column
            for datastore in self.datastores
            for schema in datastore.schemas
            for table in schema.tables
            for column in table.column_names
        ]
    
    def __repr__(self) -> str:
        descriptor: List[str] = [
            f'datastore_id={datastore.id}: [{repr(datastore)}]'
            for datastore in self.datastores
        ]
        return ' | '.join(descriptor)
    