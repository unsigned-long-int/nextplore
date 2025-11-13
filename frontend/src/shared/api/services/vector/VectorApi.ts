import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type { VectorProfileResponse } from '@/shared/api/services/vector/types.gen';

export const useVectorApi = () => {
    const http = useOrchestratorClient();
    return {
        getProfiles: (integration_id: string) =>
            http.get<VectorProfileResponse[]>(`integrations/${integration_id}/vectors/profiles`),
    }
}