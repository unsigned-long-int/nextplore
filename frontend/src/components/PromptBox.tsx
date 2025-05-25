import { Textarea, Button, Group, Paper } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';

interface Props {
  prompt: string;
  setPrompt: (val: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

export const PromptBox = ({ prompt, setPrompt, onSubmit, loading }: Props) => {
  return (
    <Paper withBorder p="md" radius="md" shadow="md">
      <Group align="flex-end">
        <Textarea
          label="Type your query"
          placeholder="e.g., Show me average expense per person for the last year for german entity"
          value={prompt}
          onChange={(e) => setPrompt(e.currentTarget.value)}
          minRows={2}
          autosize
          style={{ flexGrow: 1 }}
        />
        <Button
          leftSection={<IconSearch size={16} />}
          onClick={onSubmit}
          loading={loading}
        >
          Run
        </Button>
      </Group>
    </Paper>
  );
};