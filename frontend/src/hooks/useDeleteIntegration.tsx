import axios from "axios";

import { useTokenProvider } from "../authentication/useTokenProvider";

export const useDeleteIntegration = () => {
    const { getToken } = useTokenProvider();

    const deleteIntegration = async (id: string) => {
        const token = await getToken();
        await axios.delete(
            `http://localhost:8005/v1/nextplore-orchestrator/integrations/${id}`,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json', 
                }
            }
        );
    };
    return { deleteIntegration };
};
