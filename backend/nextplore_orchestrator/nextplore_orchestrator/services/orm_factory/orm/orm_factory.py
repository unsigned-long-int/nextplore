import asyncio
import time
import logging
from typing import Dict, List

from dataclasses import dataclass
from sqlalchemy import Column, quoted_name
from sqlalchemy.inspection import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import registry
from sqlalchemy.engine.interfaces import ReflectedColumn
from sqlalchemy.ext.declarative import declarative_base

from nextplore_orchestrator.domain.models import ORMRequest
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from nextplore_sdk.database.connection_maker.models.connection_profile import ConnectionProfile

logger = logging.getLogger(__name__)
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
    connection_profile: ConnectionProfile
    engine_manager: EngineManager

    async def generate_orm_class(self) -> type:
        Base = get_dynamic_base(self.integration_id)

        column_attrs: Dict[str, Column] = {}

        engine = await self.engine_manager.acquire_engine(self.connection_profile)

        start = time.monotonic()
        reflected_columns = await asyncio.to_thread(self._fetch_reflected_columns, engine)
        elapsed = time.monotonic() - start
        logger.info(
            'Reflected %s.%s in %.2fs (integration=%s)',
            self.schema_name,
            self.table_name,
            elapsed,
            self.integration_id
        )
        if not any(col.get('primary_key') for col in reflected_columns):
            reflected_columns[0]['primary_key'] = True

        for column in reflected_columns:
            column_attrs[column['name']] = Column(
                column['type'],
                primary_key=bool(column.get('primary_key'))
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

    def _fetch_reflected_columns(self, engine: Engine) -> List[ReflectedColumn]:
        with engine.connect() as conn:
            crawler = inspect(conn)
            return crawler.get_columns(
                table_name=quoted_name(self.table_name, quote=True),
                schema=quoted_name(self.schema_name, quote=True)
            )


async def get_orm(
    orm_request: ORMRequest,
    connection_profile: ConnectionProfile,
    engine_manager: EngineManager
) -> type:
    orm_factory = ORMFactory(
        integration_id=orm_request.integration,
        schema_name=orm_request.schema_name,
        class_name=orm_request.class_name,
        table_name=orm_request.table_name,
        connection_profile=connection_profile,
        engine_manager=engine_manager
    )
    orm_cls = await orm_factory.generate_orm_class()
    return orm_cls
    
    