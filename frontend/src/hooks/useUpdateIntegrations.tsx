import axios from 'axios';

import { useTokenProvider } from '../authentication/useTokenProvider';
import type { IntegrationUpdateRequest } from '../interface/integration/integration-update-request.interface';


export const useUpdateIntegration = () => {
    const { getToken } = useTokenProvider();

    const updateIntegration = async (id: string, data: IntegrationUpdateRequest) => {
        const token = await getToken();
        await axios.patch(
            `http://localhost:8005/v1/nextplore-orchestrator/integrations/${id}`,
            data,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json', 
                }
            }
        );
    };
    return { updateIntegration };
};
