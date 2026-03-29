import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type { VectorProfileResponse } from '@/shared/api/services/vector/types.gen';

export const useVectorApi = () => {
    const http = useOrchestratorClient();
    return {
        getProfiles: (datastore_id: string) =>
            http.get<VectorProfileResponse[]>(`datastores/${datastore_id}/vectors/profiles`),
    }
}