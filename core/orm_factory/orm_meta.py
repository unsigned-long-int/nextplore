from typing import Dict, List

from sqlalchemy import Column
from sqlalchemy.engine.interfaces import ReflectedColumn
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


def generate_orm_class(
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
    column_attrs: Dict[str, Column] = {}
    for column in reflected_columns:
        column_attrs[column['name']] = Column(
            column['type'],
            primary_key=True
        )

    return type(
        class_name,
        (Base,),
        {'__tablename__': table_name, '__table_args__': {
            'schema': schema_name},  **column_attrs}
    )
