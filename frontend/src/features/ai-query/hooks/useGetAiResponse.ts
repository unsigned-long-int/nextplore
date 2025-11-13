import { useMutation } from '@tanstack/react-query';
import { useAiQueryApi } from '@/shared/api/services/ai-query/AiQueryApi';
import type { AIQueryRequest } from '@/shared/api/services/ai-query/types.gen';

export const useGetAiResponse = () => {
    const api = useAiQueryApi();
    return useMutation({
        mutationFn: (data: AIQueryRequest)=> api.getAiResponse(data),
        mutationKey: ['ai-query-request'],
    });
};