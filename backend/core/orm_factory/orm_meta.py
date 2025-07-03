from typing import Dict, List

from sqlalchemy import Column
from sqlalchemy.engine.interfaces import ReflectedColumn
from sqlalchemy.orm import registry
from sqlalchemy.ext.declarative import declarative_base


_dynamic_bases: Dict[str, registry] = {}


def get_dynamic_base(integration_id: str):
    if integration_id not in _dynamic_bases:
        reg = registry()
        base = declarative_base(metadata=reg.metadata)
        _dynamic_bases[integration_id] = base
    return _dynamic_bases[integration_id]


def generate_orm_class(
        integration_id: str,
        schema_name: str,
        class_name: str,
        table_name: str,
        reflected_columns: List[ReflectedColumn],
) -> type:
    """
    responsible for dynamically generating orm classes
    with schema_name, class_name, table_name and column_names
    which are most likely to provide the answer to user query
    """

    Base = get_dynamic_base(integration_id)

    column_attrs: Dict[str, Column] = {}
    for column in reflected_columns:
        column_attrs[column['name']] = Column(
            column['type'],
            primary_key=True
        )

    table_identifier = f'{schema_name}.{table_name}'

    if table_identifier in Base.metadata.tables:
        Base.metadata.remove(Base.metadata.tables[table_identifier])

    if class_name in Base.registry._class_registry:
        del Base.registry._class_registry[class_name]

    return type(
        class_name,
        (Base,),
        {'__tablename__': table_name, '__table_args__': {
            'schema': schema_name}, **column_attrs}
    )
