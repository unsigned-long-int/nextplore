from typing import Dict, List

from sqlalchemy import Column
from sqlalchemy.engine.interfaces import ReflectedColumn
from sqlalchemy.orm import registry
from sqlalchemy.ext.declarative import declarative_base


mapper_registry = registry()
Base = declarative_base(metadata=mapper_registry.metadata)


def generate_orm_class(
        schema_name: str,
        class_name: str,
        table_name: str,
        reflected_columns: List[ReflectedColumn],
) -> type[Base]:
    """
    responsible for dynamically generating orm classes
    with schema_name, class_name, table_name and column_names
    which are most likely to provide the answer to user query
    """
    column_attrs: Dict[str, Column] = {}
    for column in reflected_columns:
        column_attrs[column['name']] = Column(
            column['type'],
            primary_key=True
        )

    table_identifier = f'{schema_name}.{table_name}'
    print(table_identifier)
    print(mapper_registry.metadata.tables)
    if table_identifier in mapper_registry.metadata.tables:
        print('removed')
        mapper_registry.metadata.remove(mapper_registry.metadata.tables[table_identifier])

    if class_name in mapper_registry._class_registry:
        del mapper_registry._class_registry[class_name]

    return type(
        class_name,
        (Base,),
        {'__tablename__': table_name, '__table_args__': {
            'schema': schema_name}, **column_attrs}
    )
