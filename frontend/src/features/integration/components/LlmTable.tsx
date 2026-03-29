import { ScrollArea, Table } from '@mantine/core';
import { LlmRow } from '@/features/integration/components/LlmRow.tsx';
import type { LlmProfile } from '@/shared/api/services/integration/types.gen.ts';

interface Props {
    llms: LlmProfile[];
}

export const LlmTable = ({ llms }: Props) => (
    <ScrollArea>
        <Table miw={700} verticalSpacing='sm'>
            <Table.Thead>
                <Table.Tr>
                    <Table.Th>Model</Table.Th>
                    <Table.Th>Model ID</Table.Th>
                    <Table.Th>API Base</Table.Th>
                    <Table.Th>Max Tokens</Table.Th>
                    <Table.Th />
                </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
                {llms.map((llm) => (
                    <LlmRow key={llm.model_id} llm={llm} selected={false} />
                ))}
            </Table.Tbody>
        </Table>
    </ScrollArea>
);