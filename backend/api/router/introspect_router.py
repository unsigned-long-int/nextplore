from fastapi import APIRouter
from api.models.introspect import IntrospectRequest

router = APIRouter()

@router.post("/")
def introspect_db(request: IntrospectRequest):
    return {
        "schema": {
            "tables": [
                {"name": "users", "columns": ["id", "name", "email"]},
                {"name": "orders", "columns": ["id", "user_id", "total"]}
            ]
        }
    }