from typing import Dict, List
from dataclasses import dataclass
from sqlalchemy import Column
from sqlalchemy.engine.interfaces import ReflectedColumn
from sqlalchemy.orm import registry
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import quoted_name

from shared.database.crawler import get_crawler


_dynamic_bases: Dict[str, registry] = {}


def get_dynamic_base(integration_id: str):
    if integration_id not in _dynamic_bases:
        reg = registry()
        base = declarative_base(metadata=reg.metadata)
        _dynamic_bases[integration_id] = base
    return _dynamic_bases[integration_id]


@dataclass
class ORMFactory:
    """
    responsible for dynamically generating orm classes
    with schema_name, class_name, table_name and column_names
    which are most likely to provide the answer to user query
    """
    integration_id: str
    schema_name: str
    class_name: str
    table_name: str

    def generate_orm_class(self) -> type:
        Base = get_dynamic_base(self.integration_id)

        column_attrs: Dict[str, Column] = {}
        for column in self._fetch_reflected_columns():
            column_attrs[column['name']] = Column(
                column['type'],
                primary_key=True
            )

        table_identifier = f'{self.schema_name}.{self.table_name}'

        if table_identifier in Base.metadata.tables:
            Base.metadata.remove(Base.metadata.tables[table_identifier])

        if self.class_name in Base.registry._class_registry:
            del Base.registry._class_registry[self.class_name]

        return type(
            self.class_name,
            (Base,),
            {'__tablename__': self.table_name, '__table_args__': {
                'schema': self.schema_name}, **column_attrs}
        )

    def _fetch_reflected_columns(self) -> List[ReflectedColumn]:
        crawler = get_crawler(self.integration_id)
        return crawler.get_columns(
            table_name=quoted_name(self.table_name, quote=True),
            schema=quoted_name(self.schema_name, quote=True)
        )
