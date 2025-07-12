from fastapi import APIRouter

from api.models import FilteredInspectionRequest, InspectionResponse
from api.handlers import handle_filtered_inspection


router = APIRouter(prefix='/v1/inspection', tags=['Inspection'])

@router.post('/inspect-filtered', response_model=InspectionResponse)
def inspect_filtered(request: FilteredInspectionRequest) -> InspectionResponse:
    return handle_filtered_inspection(request)
