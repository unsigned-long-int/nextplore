from typing import Dict, List
from pydantic import BaseModel, UUID4


class FilteredInspectionRequest(BaseModel):
    integrations: List[UUID4]
    schemas: Dict[UUID4, List[str]]
    tables: Dict[UUID4, List[str]]
