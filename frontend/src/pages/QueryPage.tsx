import {
  Box,
  Divider,
  Loader,
  Text,
  Title,
  Transition,
} from '@mantine/core';
import { useState } from 'react';
import { PromptBox } from '../components/ai_queries/PromptBox';
import { QueryPreview } from '../components/ai_queries/QueryPreview';
import { ResultTable } from '../components/ai_queries/ResultTable';
import { askQuery } from '../services/api';

export const QueryPage = () => {
  const [prompt, setPrompt] = useState('');
  const [sqlPreview, setSqlPreview] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);


  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await askQuery(prompt);
      setResults(res.data);
      setSqlPreview(res.sql);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
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
        onSubmit={handleSubmit}
        loading={loading}
      />

      <Divider my="lg" />

      {loading && <Loader variant="bars" />}

      <Transition mounted={!loading && !!sqlPreview} transition="fade" duration={400}>
        {(styles) => (
          <div style={styles}>
            <QueryPreview sql={sqlPreview} />
            <ResultTable data={results} />
          </div>
        )}
      </Transition>
    </Box>
  );
};