import { Paper, Code, Title } from '@mantine/core';

export const QueryPreview = ({ sql }: { sql: string }) => {
  if (!sql) return null;
  return (
    <Paper shadow="xs" p="md" withBorder mb="md">
      <Title order={5} mb="xs">Generated SQL</Title>
      <Code block>{sql}</Code>
    </Paper>
  );
};