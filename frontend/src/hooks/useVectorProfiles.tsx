import axios from 'axios';

import { useTokenProvider } from '../authentication/useTokenProvider';
import type { VectorProfileRequest } from '../interface/vector-profile-request.interface';

export const useVectorProfiles = () => {
    const { getToken } = useTokenProvider();

    const fetchVectorProfiles = async(vector_profile_request: VectorProfileRequest) => {
        const token = await getToken();

        const response = await axios.post(
            'http://localhost:8005/nextplore-orchestrator/vector-profiles', 
            vector_profile_request,
            {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        return response.data;
    };
    return { fetchVectorProfiles };
}