
from pydantic import BaseModel


class CrawlResponse(BaseModel):
    integration_registry_repr: str
    integrations_enum: list[str]
    schemas_enum: list[str]
    tables_enum: list[str]
    columns_enum: list[str]
    filter_op_enum: list[str]
    agg_funcs_enum: list[str]
