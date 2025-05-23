from sqlalchemy import select, inspect
from sqlalchemy.sql import operators
from typing import Any, List, Dict

def generate_orm_statement(
    model: type,
    filters: List[Dict[str, Any]]
):
    stmt = select(model)

    for cond in filters:
        field = getattr(model, cond['filter_column'])
        op = cond['operator']
        value = cond['value']
        print(op)
        print(value)

        if op == '==':
            stmt = stmt.where(field == value)
        elif op == '>':
            stmt = stmt.where(field > value)
        elif op == '<':
            stmt = stmt.where(field < value)
        elif op == '>=':
            stmt = stmt.where(field >= value)
        elif op == '<=':
            stmt = stmt.where(field <= value)
        elif op == 'like':
            stmt = stmt.where(field.like(value))
        elif op == 'in':
            stmt = stmt.where(field.in_(value))
        else:
            raise ValueError(f"Unsupported operator: {op}")

    return stmt