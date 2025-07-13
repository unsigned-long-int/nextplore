import httpx
import os
from typing import Dict, List
from uuid import UUID

from shared.contracts.integration_service import (
    FilteredInspectionRequest, 
    InitialInspectionRequest,
    InspectionResponse
)
    


class IntegrationRegistryInspectionClient:
    def __init__(self, base_url: str = f'http://inspection_service:8001') -> None:
        self.base_url = base_url
        self.session = httpx.Client(timeout=5.0)

    def fetch_filtered_integration_registry(
            self, 
            integrations: List[UUID], 
            schemas: Dict[UUID, List[str]], 
            tables: Dict[UUID, List[str]]
    ) -> InspectionResponse:
        print(f'fetch filtered received: {integrations}')
        print(f'fetch tables: {tables}')
        payload = FilteredInspectionRequest(
            integrations=integrations,
            schemas=schemas,
            tables=tables
        )
        response = self.session.post(
            f'{self.base_url}/v1/inspection/inspect-filtered', 
            data=payload.model_dump_json(),
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return InspectionResponse(**response.json())
    
    def inspect_initial_integation(self, integration_id: UUID) -> None:
        payload = InitialInspectionRequest(integration_id=integration_id)
        print(f'posting to inspect-initial: {payload}')
        response = self.session.post(
            f'{self.base_url}/v1/inspection/inspect-initial', 
            data=payload.model_dump_json(),
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
