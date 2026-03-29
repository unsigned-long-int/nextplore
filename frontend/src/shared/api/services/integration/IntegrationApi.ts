import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type {
    DataStoreCreateRequest,
    DataStoreTestResponse,
    DataStoreUpdateRequest,
    DataStoreProfile,
    LlmModelCreateRequest,
    LlmProfile
} from '@/shared/api/services/integration/types.gen';

export const useIntegrationApi = () => {
    const http = useOrchestratorClient();
    return {
        testDatastore: (data: DataStoreCreateRequest) =>
            http.post<DataStoreTestResponse>('datastores/test', data),
        createDatastore: (data: DataStoreCreateRequest) =>
            http.post<void>('datastores', data),
        deleteDatastore: (id: string) =>
            http.delete<void>(`datastores/${id}`),
        updateDatastore: (id: string, data: DataStoreUpdateRequest) =>
            http.patch<void>(`datastores/${id}`, data),
        getDatastoreProfiles: () =>
            http.get<DataStoreProfile[]>('datastores/profiles'),
        createLlm: (data: LlmModelCreateRequest) =>
            http.post<void>('llm', data),
        getLlmProfiles: () =>
            http.get<LlmProfile[]>('llm/profiles'),
    };
};