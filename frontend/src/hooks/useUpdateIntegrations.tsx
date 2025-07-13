import axios from "axios";

import { useTokenProvider } from "../authentication/useTokenProvider";
import type { IntegrationUpdateRequest } from "../interface/integration-update-request";


export const useUpdateIntegration = () => {
    const { getToken } = useTokenProvider();

    const updateIntegration = async (data: IntegrationUpdateRequest) => {
        const token = await getToken();
        const response = await axios.post(
            'http://localhost:8003/nextplore-orchestrator/updateintegration',
            data,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json', 
                }
            }
        );
        return response.data;
    };
    return { updateIntegration };
};
