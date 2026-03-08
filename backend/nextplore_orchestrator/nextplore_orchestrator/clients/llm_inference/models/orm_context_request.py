from pydantic import BaseModel, UUID4
from typing import List


class Context(BaseModel):
    integration_registry_repr: str 
    integrations_enum: List[str]
    schemas_enum: List[str]
    tables_enum: List[str]
    columns_enum: List[str]
    filter_op_enum: List[str]
    agg_funcs_enum: List[str]


class ORMContextRequest(BaseModel):
    provider: str
    model_id: str
    query: str
    context: Context
