import { useQuery } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';


export const useIntegrationProfiles = () => {
    const api = useIntegrationApi();
    return useQuery({
        queryKey: ['integration-profiles'],
        queryFn: () => api.getProfiles(),
    });
};
