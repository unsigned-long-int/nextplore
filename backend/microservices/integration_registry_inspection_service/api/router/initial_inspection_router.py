from fastapi import APIRouter

from api.models import InitialInspectionRequest, InspectionResponse
from api.handlers import handle_initial_inspection


router = APIRouter(prefix='/v1/inspection', tags=['Inspection'])

@router.post('/inspect-initial', response_model=InspectionResponse)
def inspect_filtered(request: InitialInspectionRequest) -> None:
    handle_initial_inspection(request)
    