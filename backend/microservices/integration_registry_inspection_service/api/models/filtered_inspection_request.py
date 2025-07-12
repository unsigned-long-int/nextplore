from typing import Dict, List
from pydantic import BaseModel 


class FilteredInspectionRequest(BaseModel):
    integrations: List[str]
    schemas: Dict[str, List[str]]
    tables: Dict[str, List[str]]
