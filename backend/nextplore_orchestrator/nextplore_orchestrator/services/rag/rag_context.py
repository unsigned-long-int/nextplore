from typing import List
from pydantic import BaseModel, Field


class RAGContext(BaseModel):
    integration_registry_repr: str 
    integrations_enum: List[str]
    schemas_enum: List[str]
    tables_enum: List[str]
    columns_enum: List[str]
    filter_op_enum: List[str] = Field(default=['==', '!=', '>', '<', '>=', '<=', 'like', 'not like', 'in'])
    agg_funcs_enum: List[str] = Field(default=['sum', 'avg', 'min', 'max', 'count'])
