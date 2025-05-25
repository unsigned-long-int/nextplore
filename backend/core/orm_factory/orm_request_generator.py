from sqlalchemy import select, func, Select
from typing import Any, Dict, List
from .ai_orm_factory import ORMRequest

OPERATOR_DISPATCHER: Dict[str, Any] = {
    '==': lambda stmt, field, value: stmt.where(field == value),
    '!=': lambda stmt, field, value: stmt.where(field != value),
    '>': lambda stmt, field, value: stmt.where(field > value),
    '<': lambda stmt, field, value: stmt.where(field < value),
    '>=': lambda stmt, field, value: stmt.where(field >= value),
    '<=': lambda stmt, field, value: stmt.where(field <= value),
    'like': lambda stmt, field, value: stmt.where(field.like(value)),
    'not like': lambda stmt, field, value: stmt.where(~field.like(value)),
    'in': lambda stmt, field, value: stmt.where(field.in_(value))
    }

AGGREGATOR_DISPATCHER: Dict[str, Any] = {
    'sum': func.sum,
    'avg': func.avg,
    'min': func.min,
    'max': func.max,
    'count': func.count
}

def aggregate(orm_request) -> Select:
    aggregate_columns = [aggregator['agg_column'] for aggregator in orm_request.aggregates]
    columns = [getattr(orm_request.orm_model, column) for column in orm_request.selected_columns if column not in aggregate_columns]
    for agg in orm_request.aggregates:
        agg_func = agg['agg_func']
        agg_column = agg['agg_column']
        if agg_func not in AGGREGATOR_DISPATCHER:
            raise ValueError(f'Unsupported aggregate: {agg}')
        
        aggregate_expression = AGGREGATOR_DISPATCHER[agg_func](getattr(orm_request.orm_model, agg_column)).label(f'{agg_func}_{agg_column}')
        columns.append(aggregate_expression)
    stmt = select(*columns)
    stmt = stmt.group_by(*[getattr(orm_request.orm_model, column) 
                           for column in orm_request.selected_columns 
                           if column not in aggregate_columns])
    return stmt

def apply_filter(orm_request: ORMRequest, stmt: Select) -> Select:
    for cond in orm_request.filters:
        field = getattr(orm_request.orm_model, cond['filter_column'])
        op = cond['operator']
        value = cond['value']
        if op not in OPERATOR_DISPATCHER:
            raise ValueError(f'Unsupported operator: {op}')
        stmt = OPERATOR_DISPATCHER[op](stmt, field, value)
    return stmt


def generate_orm_statement(orm_request: ORMRequest) -> Select:
    model = orm_request.orm_model
    aggregates = orm_request.aggregates
    filters = orm_request.filters
    
    if aggregates:
        stmt = aggregate(orm_request)
    else:
        columns = [getattr(model, column) for column in orm_request.selected_columns]
        stmt = select(*columns)
    if filters:
        stmt = apply_filter(orm_request, stmt)
    return stmt