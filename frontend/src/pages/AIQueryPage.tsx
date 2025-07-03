import { useState } from 'react';
import {
    Title,
    Text,
    Box,
    Loader,
    Divider,
    Transition
} from '@mantine/core';
import { PromptBox } from '../components/PromptBox';
import { QueryPreview } from '../components/QueryPreview';
import { ResultTable } from '../components/ResultTable';

import { useAIQueryRequest } from "../hooks/useAIQueryRequest";
import type { AIQueryRequest } from "../interface/ai-query-request.interface";

export const AIQueryPage = () => {
    const [prompt, setPrompt] = useState<string>('');
    const [aiQueryResponse, setAIQueryResponse] = useState<{[key: string]: string}[]>([]);
    const [sqlPreview, setSqlPreview] = useState<string>('');
    const [querying, setQuerying] = useState<boolean>(false);
    const { getAIQueryResponse } = useAIQueryRequest();

    const handleAIQueryRequest = async () => {
        setQuerying(true);
        try {
            const response = await getAIQueryResponse(prompt);
            setAIQueryResponse(response.data);
            setSqlPreview(response.sql);
        } catch (err) {
            console.error(err);
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
          <PromptBox
            prompt={prompt}
            setPrompt={setPrompt}
            onSubmit={handleAIQueryRequest}
            loading={querying}
          />
    
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