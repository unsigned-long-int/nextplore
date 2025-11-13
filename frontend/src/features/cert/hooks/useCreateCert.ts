import { useQueryClient, useMutation } from '@tanstack/react-query';
import { useCertApi } from '@/shared/api/services/cert/CertApi';
import type { CertCreateRequest } from '@/shared/api/services/cert/types.gen';


export const useCreateCert = () => {
    const api = useCertApi();
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (data: CertCreateRequest) => api.createCert(data),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['cert-profiles'] });
        },
    });
};