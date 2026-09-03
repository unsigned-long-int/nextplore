from typing import Any

from pydantic import ValidationError
from svc_llm_inference_contracts.models import ORMContextResponse

from llm_inference_service.services.models_gateway.exceptions import (
    InvalidModelResponse,
)


def parse_response_schema(
    model_response: dict[str, Any], model_id: str, provider_name: str
) -> dict[str, Any]:
    if "column_names" not in model_response or not model_response["column_names"]:
        msg = f"Missing or empty column_names in response. Model: {model_id}. Provider: {provider_name}. Response: {model_response}"
        raise InvalidModelResponse(msg)

    first_col = model_response["column_names"][0]
    parts = first_col.split(".")
    schema_name, table_name = parts[0], parts[1]

    for col in model_response["column_names"]:
        if not col.startswith(f"{schema_name}.{table_name}."):
            msg = f"Parsing failed. Column {col} does not belong to {schema_name}.{table_name}. Model: {model_id}. Provider: {provider_name}, Response: {model_response}"
            raise InvalidModelResponse(msg)

    parsed = {
        "datastore": model_response["datastore"],
        "class_name": model_response["class_name"],
        "schema_name": schema_name,
        "table_name": table_name,
        "column_names": [c.split(".")[2] for c in model_response["column_names"]],
        "column_filters": [
            {**f, "filter_column": f["filter_column"].split(".")[2]}
            for f in model_response["column_filters"]
        ],
        "column_aggregates": [
            {**a, "agg_column": a["agg_column"].split(".")[2]}
            for a in model_response["column_aggregates"]
        ],
    }
    try:
        ORMContextResponse(**parsed)
    except ValidationError:
        raise InvalidModelResponse(
            f"Schema validation failed. Model: {model_id}. "
            f"Provider: {provider_name}. Response: {parsed}"
        )

    return parsed
