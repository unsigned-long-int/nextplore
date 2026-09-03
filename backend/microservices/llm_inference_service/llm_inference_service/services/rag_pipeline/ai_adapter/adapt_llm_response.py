from typing import Any

from llm_inference_service.domain.models.orm_context import ORMContext


def adapt_llm_response(response: dict[str, Any]) -> ORMContext:
    return ORMContext(
        datastore=response["datastore"],
        schema_name=response["schema_name"],
        class_name=response["class_name"],
        table_name=response["table_name"],
        column_names=response["column_names"],
        column_filters=response["column_filters"],
        column_aggregates=response["column_aggregates"],
    )
