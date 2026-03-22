import { useMutation } from '@tanstack/react-query';
import { useAiQueryApi } from '@/shared/api/services/ai-query/AiQueryApi';
import type { PromptRequest } from '@/shared/api/services/ai-query/types.gen';

export const useGetDescriptionEnhancement = () => {
    const api = useAiQueryApi();
    return useMutation({
        mutationFn: (data: PromptRequest)=> api.getDescriptionEnhancement(data),
        mutationKey: ['ai-query-request'],
    });
};