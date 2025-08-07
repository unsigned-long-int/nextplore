from typing import Dict, Any
from services.orm_context_builder.orm_context_model import ORMContext



def adapt_llm_response(response: Dict[str, Any]) -> ORMContext:
    return ORMContext(
        integration=response['integration'],
        schema_name=response['schema_name'],
        class_name=response['class_name'],
        table_name=response['table_name'],
        column_names=response['column_names'],
        column_filters=response['column_filters'],
        column_aggregates=response['column_aggregates']
    )
