import { useQuery } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';


export const useDatastoreProfiles = () => {
    const api = useIntegrationApi();
    return useQuery({
        queryKey: ['datastore-profiles'],
        queryFn: () => api.getDatastoreProfiles(),
    });
};
