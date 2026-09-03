from typing import Any

from sqlalchemy import Select, func, select

from nextplore_orchestrator.domain.models.statement_request import StatementRequest

OPERATOR_DISPATCHER: dict[str, Any] = {
    "==": lambda stmt, field, value: stmt.where(field == value),
    "!=": lambda stmt, field, value: stmt.where(field != value),
    ">": lambda stmt, field, value: stmt.where(field > value),
    "<": lambda stmt, field, value: stmt.where(field < value),
    ">=": lambda stmt, field, value: stmt.where(field >= value),
    "<=": lambda stmt, field, value: stmt.where(field <= value),
    "like": lambda stmt, field, value: stmt.where(field.like(value)),
    "not like": lambda stmt, field, value: stmt.where(~field.like(value)),
    "in": lambda stmt, field, value: stmt.where(field.in_(value)),
}

AGGREGATOR_DISPATCHER: dict[str, Any] = {
    "sum": func.sum,
    "avg": func.avg,
    "min": func.min,
    "max": func.max,
    "count": func.count,
}


def aggregate(statement_request: StatementRequest) -> Select:
    aggregate_columns = [
        aggregator["agg_column"] for aggregator in statement_request.column_aggregates
    ]
    columns = [
        getattr(statement_request.orm_model, column)
        for column in statement_request.column_names
        if column not in aggregate_columns
    ]
    for agg in statement_request.column_aggregates:
        agg_func = agg["agg_func"]
        agg_column = agg["agg_column"]
        if agg_func not in AGGREGATOR_DISPATCHER:
            raise ValueError(f"Unsupported aggregate: {agg}")

        aggregate_expression = AGGREGATOR_DISPATCHER[agg_func](
            getattr(statement_request.orm_model, agg_column)
        ).label(f"{agg_func}_{agg_column}")
        columns.append(aggregate_expression)
    stmt = select(*columns)
    stmt = stmt.group_by(
        *[
            getattr(statement_request.orm_model, column)
            for column in statement_request.column_names
            if column not in aggregate_columns
        ]
    )
    return stmt


def apply_filter(statement_request: StatementRequest, stmt: Select) -> Select:
    for cond in statement_request.column_filters:
        field = getattr(statement_request.orm_model, cond["filter_column"])
        op = cond["operator"]
        value = cond["value"]

        if op not in OPERATOR_DISPATCHER:
            raise ValueError(f"Unsupported operator: {op}")

        if op == "in" and isinstance(value, str):
            value = [v.strip() for v in value.split(",")]

        stmt = OPERATOR_DISPATCHER[op](stmt, field, value)
    return stmt


def get_statement(statement_request: StatementRequest) -> Select:
    model = statement_request.orm_model
    aggregates = statement_request.column_aggregates
    filters = statement_request.column_filters

    if aggregates:
        stmt = aggregate(statement_request)
    else:
        columns = [getattr(model, column) for column in statement_request.column_names]
        stmt = select(*columns)
    if filters:
        stmt = apply_filter(statement_request, stmt)
    return stmt
