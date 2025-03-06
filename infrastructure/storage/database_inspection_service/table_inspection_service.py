from sqlalchemy import Inspector
from typing import Dict, Set, Optional

from infrastructure.event_orchestration_service.event_orchestrator import EventOrchestrator
from infrastructure.event_orchestration_service.events import events
from .table_descriptor import TableDescriptor


class TableDescriptorGeneratorError(Exception):
    pass


def fetch_table(
        inspector: Inspector,
        schema_name: str,
        table_name: str
) -> Dict[str, TableDescriptor]:
    try:
        table = {
            table_name: TableDescriptor(
                inspector.get_columns(
                    table_name=table_name, schema=schema_name),
                primary_keys=inspector.get_pk_constraint(
                    table_name=table_name, schema=schema_name),
                foreign_keys=inspector.get_foreign_keys(
                    table_name=table_name, schema=schema_name),
                indexes=inspector.get_indexes(
                    table_name=table_name, schema=schema_name),
                table_comment=inspector.get_table_comment(
                    table_name=table_name, schema=schema_name)
            )
        }
        return table
    except Exception as e:
        message = f'Error: {str(e)}. Failed for: {table_name}'
        raise TableDescriptorGeneratorError(message) from e
