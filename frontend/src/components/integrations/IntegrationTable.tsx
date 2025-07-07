import { Checkbox, ScrollArea, Table } from '@mantine/core';
import type { IntegrationProfile } from '../../interface/integration-profile.interface';
import { IntegrationRow } from './IntegrationRow';


interface Props {
  integrations: IntegrationProfile[];
  selection: string[];
  toggleRow: (id: string) => void;
  toggleAll: () => void;
  onToggleAutosync: (index: number, checked: boolean) => void;
  onDelete: (id: string) => void;
}


export const IntegrationTable = ({ integrations, selection, toggleRow, toggleAll, onToggleAutosync, onDelete }: Props) => (
    <ScrollArea>
        <Table miw={800} verticalSpacing="sm">
        <Table.Thead>
            <Table.Tr>
            <Table.Th w={40}>
                <Checkbox
                onChange={toggleAll}
                checked={selection.length === integrations.length}
                indeterminate={selection.length > 0 && selection.length !== integrations.length}
                />
            </Table.Th>
            <Table.Th>Service Type</Table.Th>
            <Table.Th>Connection Name</Table.Th>
            <Table.Th>Database Name</Table.Th>
            <Table.Th>Authentication Method</Table.Th>
            <Table.Th>Auto Sync</Table.Th>
            <Table.Th>Options</Table.Th>
            </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
            {integrations.map((integration, index) => (
            <IntegrationRow
                key={integration.id}
                integration={integration}
                index={index}
                selected={selection.includes(integration.id)}
                toggleRow={toggleRow}
                onToggleAutosync={onToggleAutosync}
                onDelete={onDelete}
            />
            ))}
        </Table.Tbody>
        </Table>
    </ScrollArea>
);