import {
    Box,
    Divider,
    Loader,
    Select,
    Text,
    Title,
    Transition
} from '@mantine/core';
import { useEffect, useState } from 'react';
import { PromptBox } from '../components/ai_queries/PromptBox';
import { QueryPreview } from '../components/ai_queries/QueryPreview';
import { ResultTable } from '../components/ai_queries/ResultTable';

import { useAIGenerativeModels } from '../hooks/useAIGenerativeModels';
import { useAIQueryRequest } from "../hooks/useAIQueryRequest";
import type { ModelInfo } from '../interface/ai-generative-models-response.interface';
import type { AIQueryRequest } from '../interface/ai-query-request.interface';

export const AIQueryPage = () => {
    const [prompt, setPrompt] = useState<string>('');
    const [selectedModel, setSelectedModel] = useState<string | null>(null);
    const [modelOptions, setModelOptions] = useState<{ value: string; label: string }[]>([]);
    const [aiQueryResponse, setAIQueryResponse] = useState<{[key: string]: string}[]>([]);
    const [sqlPreview, setSqlPreview] = useState<string>('');
    const [querying, setQuerying] = useState<boolean>(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const { getAIQueryResponse } = useAIQueryRequest();
    const { getAIGenerativeModels } = useAIGenerativeModels();


    useEffect(() => {
        getAIGenerativeModels().then((models) => {
        const options = models.map((m: ModelInfo) => ({
            value: m.model_id,
            label: `${m.label} (${m.tags.join(', ')})`,
        }));
        setModelOptions(options);
        setSelectedModel(options[0]?.value || null);
        });
    }, []);

    const handleAIQueryRequest = async () => {
        if (!selectedModel) return;
        setQuerying(true);
        setAIQueryResponse([]);
        setSqlPreview('');
        setErrorMessage(null);
        try {
            const request: AIQueryRequest = {
                model_id: selectedModel,
                prompt
              };
            const response = await getAIQueryResponse(request);
            setAIQueryResponse(response.data);
            setSqlPreview(response.sql);
        } catch (e: any) {
            console.error(e);
            setErrorMessage(e.message);
        } finally {
            setQuerying(false);
        }
    };

    return (
        <Box>
            <Title order={2} mb="xs">Request any data from database</Title>
            <Text c="dimmed" size="sm" mb="md">
                Example: "Total number of employees in german payroll"
            </Text>
            <Box w={300} ml="auto" mb="md">
                <Select
                    label="Choose LLM Model"
                    placeholder="Pick a model"
                    searchable
                    withAsterisk
                    nothingFoundMessage="No models"
                    data={modelOptions}
                    value={selectedModel}
                    onChange={setSelectedModel}
                />
            </Box>
            <PromptBox
                prompt={prompt}
                setPrompt={setPrompt}
                onSubmit={handleAIQueryRequest}
                loading={querying}
            />
            {errorMessage && (
                <Box my="sm">
                    <Text c="red" size="sm" ta="center">
                        {errorMessage}
                    </Text>
                </Box>
            )}
            <Divider my="lg" />
                {querying && <Loader variant="bars" />}
            <Transition mounted={!querying && !!sqlPreview} transition="fade" duration={400}>
                {(styles) => (
                <div style={styles}>
                    <QueryPreview sql={sqlPreview} />
                    <ResultTable data={aiQueryResponse} />
                </div>
            )}
            </Transition>
        </Box>
      );
    };