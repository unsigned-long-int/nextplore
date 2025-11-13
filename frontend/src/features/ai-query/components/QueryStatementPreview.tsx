import { Code, Paper, Title } from '@mantine/core';

import { QueryStatementCopyButton } from '@/features/ai-query/components/QueryStatementCopyButton';

export const QueryStatementPreview = ({ sql }: { sql: string }) => {
    if (!sql) return null;
    return (
        <Paper shadow='xs' p='md' withBorder mb='md'>
            <Title order={5} mb='xs'>Generated SQL</Title>
            <div style={{ position: 'absolute', top: 12, right: 12 }}>
                <QueryStatementCopyButton sql={sql} />
            </div>
            <Code block mt='md'>{sql}</Code>
        </Paper>
    );
};
