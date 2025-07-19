import axios from 'axios';

import { useTokenProvider } from '../authentication/useTokenProvider';
import type { VectorMetadataRequest } from '../interface/vector-request.interface';

export const useVectorMetadata = () => {
    const { getToken } = useTokenProvider();

    const fetchVectorMetadata = async(vector_metadata_request: VectorMetadataRequest) => {
        const token = await getToken();

        const response = await axios.post(
            'http://localhost:8004/nextplore-orchestrator/vector-metadata', 
            vector_metadata_request,
            {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        return response.data;
    };
    return { fetchVectorMetadata };
}