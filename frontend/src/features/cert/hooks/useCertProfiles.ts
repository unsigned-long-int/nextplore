import { useQuery } from '@tanstack/react-query';
import { useCertApi } from '@/shared/api/services/cert/CertApi';


export const useCertProfiles = () => {
    const api = useCertApi()
    return useQuery({
        queryKey: ['cert-profiles'],
        queryFn: () => api.getProfiles(),
    });
};