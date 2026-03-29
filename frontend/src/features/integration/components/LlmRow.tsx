import { Group, Table, Text } from '@mantine/core';
import cx from 'clsx';
import classes from '@/styles/IntegrationsList.module.css';
import { LlmProviderIcon } from '@/features/integration/components/LlmProviderIcon.tsx';
import { LlmActionsMenu } from '@/features/integration/components/LlmActionsMenu.tsx';
import type { LlmProfile } from '@/shared/api/services/integration/types.gen.ts';

interface Props {
    llm: LlmProfile;
    selected: boolean;
}

export const LlmRow = ({ llm, selected }: Props) => (
    <Table.Tr className={cx({ [classes.rowSelected]: selected })}>
        <Table.Td>
            <Group gap='sm'>
                <LlmProviderIcon modelId={llm.model_id} size={16} />
                <Text size='sm' fw={500}>{llm.label}</Text>
            </Group>
        </Table.Td>
        <Table.Td>
            <Text size='sm' c='dimmed' ff='monospace'>{llm.model_id}</Text>
        </Table.Td>
        <Table.Td>
            <Text size='sm' c='dimmed'>{llm.api_base}</Text>
        </Table.Td>
        <Table.Td>
            <Text size='sm'>{llm.max_tokens.toLocaleString()}</Text>
        </Table.Td>
        <Table.Td>
            <LlmActionsMenu />
        </Table.Td>
    </Table.Tr>
);