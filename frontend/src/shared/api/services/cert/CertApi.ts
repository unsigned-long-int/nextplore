import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type { CertProfile, CertCreateRequest } from '@/shared/api/services/cert/types.gen';


export const useCertApi = () => {
    const http = useOrchestratorClient();
    return {
        getProfiles: () =>
            http.get<CertProfile[]>('datastores/certificates/profiles'),
        createCert: (data: CertCreateRequest) =>
            http.post<void>('datastores/certificates', data),
    }
}