import axios from "axios";

import { useTokenProvider } from "../authentication/useTokenProvider";
import type { IntegrationDeleteRequest } from "../interface/integration-delete-request.interface";


export const useDeleteIntegration = () => {
    const { getToken } = useTokenProvider();

    const deleteIntegration = async (integration_delete_request: IntegrationDeleteRequest) => {
        const token = await getToken();
        const response = await axios.post(
            '/api/deleteintegration',
            integration_delete_request,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json', 
                }
            }
        );
        return response.data;
    };
    return { deleteIntegration };
};
