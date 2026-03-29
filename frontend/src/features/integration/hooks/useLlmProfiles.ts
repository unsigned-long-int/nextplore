import { useQuery } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';


export const useLlmProfiles = () => {
    const api = useIntegrationApi();
    return useQuery({
        queryKey: ['llm-profiles'],
        queryFn: () => api.getLlmProfiles(),
    });
};
