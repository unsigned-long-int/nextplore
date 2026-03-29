import { Text } from '@mantine/core';
import { LlmTable } from '@/features/integration/components/LlmTable.tsx';
import { useLlmProfiles } from '@/features/integration/hooks/useLlmProfiles.ts';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';

export const LlmList = () => {
    const { isLoading, isError, data = [] } = useLlmProfiles();

    if (isLoading) return <LoadingOverlay loadingText='Loading LLM models...' />;
    if (isError) return <Text c='red'>Failed to load LLM models</Text>;
    if (!data.length) return <Text c='dimmed'>No LLM models connected yet.</Text>;

    return <LlmTable llms={data} />;
};