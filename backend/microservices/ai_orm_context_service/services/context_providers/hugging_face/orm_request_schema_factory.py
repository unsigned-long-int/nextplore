from pydantic import BaseModel, create_model
from typing import Type, Optional, List

from .build_enum import build_enum
from shared.contracts.ai_orm_context_service import ORMContextRequest


def get_orm_request_schema(orm_context_request: ORMContextRequest) -> Type[BaseModel]:
    IntegrationEnum = build_enum('IntegrationEnum', orm_context_request.context.integrations_enum)
    SchemaEnum = build_enum('SchemaEnum', orm_context_request.context.schemas_enum)
    TableEnum = build_enum('TableEnum', orm_context_request.context.tables_enum)
    ColumnEnum = build_enum('ColumnEnum', orm_context_request.context.columns_enum)
    FilterOpEnum = build_enum('FilterOpEnum', orm_context_request.context.filter_op_enum)
    AggFuncEnum = build_enum('AggFuncEnum', orm_context_request.context.agg_funcs_enum)

    ColumnFilter = create_model(
        'ColumnFilter',
        operator=(FilterOpEnum, ...),
        value=(str | float, ...),
        filter_column=(ColumnEnum, ...)
    )

    ColumnAggregate = create_model(
        'ColumnAggregate',
        agg_func=(AggFuncEnum, ...),
        agg_column=(ColumnEnum, ...)
    )

    FunctionCall = create_model(
        'FunctionCall',
        function=(str, 'generate_orm_class'),
        integration=(IntegrationEnum, ...),
        schema_name=(SchemaEnum, ...),
        table_name=(TableEnum, ...),
        class_name=(str, ...),
        column_names=(List[ColumnEnum], ...),
        column_filters=(Optional[List[ColumnFilter]], []),
        column_aggregates=(Optional[List[ColumnAggregate]], []),
    )

    return FunctionCall 
