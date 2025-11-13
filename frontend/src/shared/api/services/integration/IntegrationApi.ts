import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type {
    IntegrationCreateRequest,
    IntegrationTestResponse,
    IntegrationUpdateRequest,
    IntegrationProfile } from '@/shared/api/services/integration/types.gen';

export const useIntegrationApi = () => {
    const http = useOrchestratorClient();
    return {
        testIntegration: (data: IntegrationCreateRequest) =>
            http.post<IntegrationTestResponse>('integrations/test', data),
        createIntegration: (data: IntegrationCreateRequest) =>
            http.post<void>('integrations', data),
        deleteIntegration: (id: string) =>
            http.delete<void>(`integrations/${id}`),
        updateIntegration: (id: string, data: IntegrationUpdateRequest) =>
            http.patch<void>(`integrations/${id}`, data),
        getProfiles: () =>
            http.get<IntegrationProfile[]>('integrations/profiles'),
    };
};