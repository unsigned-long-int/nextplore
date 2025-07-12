import httpx
import os
from typing import Dict, List
from uuid import UUID

from microservices.integration_registry_inspection_service.api.models import (
    FilteredInspectionRequest, 
    InitialInspectionRequest,
    InspectionResponse
)
    


class IntegrationRegistryInspectionClient:
    def __init__(self, base_url: str = f'http://localhost:{os.getenv('INSPECTION_PORT')}') -> None:
        self.base_url = base_url
        self.session = httpx.Client(timeout=5.0)

    def fetch_filtered_integration_registry(
            self, 
            integrations: List[UUID], 
            schemas: Dict[str, List[str]], 
            tables: Dict[str, List[str]]
    ) -> InspectionResponse:
        payload = FilteredInspectionRequest(
            integrations=integrations,
            schemas=schemas,
            tables=tables
        )
        response = self.session.post(f'{self.base_url}/inspect-filtered', json=payload)
        response.raise_for_status()
        return InspectionResponse(**response.json())
    
    def inspect_initial_integation(self, integration_id: UUID) -> None:
        payload = InitialInspectionRequest(integration_id=integration_id)
        response = self.session.post(f'{self.base_url}/inspect-initial', json=payload)
        response.raise_for_status()
