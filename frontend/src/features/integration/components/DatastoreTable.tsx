import { Checkbox, ScrollArea, Table } from '@mantine/core';

import { DatastoreRow } from './DatastoreRow';
import type { DataStoreProfile } from '@/shared/api/services/integration/types.gen';



interface Props {
  datastores: DataStoreProfile[];
  selection: string[];
  toggleRow: (id: string) => void;
  toggleAll: () => void;
  onToggleAutosync: (index: number, checked: boolean) => void;
  onDelete: (id: string) => void;
}


export const DatastoreTable = ({ datastores, selection, toggleRow, toggleAll, onToggleAutosync, onDelete }: Props) => (
    <ScrollArea>
        <Table miw={800} verticalSpacing="sm">
        <Table.Thead>
            <Table.Tr>
            <Table.Th w={40}>
                <Checkbox
                onChange={toggleAll}
                checked={selection.length === datastores.length}
                indeterminate={selection.length > 0 && selection.length !== datastores.length}
                />
            </Table.Th>
            <Table.Th>DB</Table.Th>
            <Table.Th>Auth</Table.Th>
            <Table.Th>Cloud</Table.Th>
            <Table.Th>Connection Name</Table.Th>
            <Table.Th>Database Name</Table.Th>
            <Table.Th>Host</Table.Th>
            <Table.Th>Port</Table.Th>
            <Table.Th>Auto Sync</Table.Th>
            </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
            {datastores.map((datastore, index) => (
            <DatastoreRow
                key={datastore.id}
                datastore={datastore}
                index={index}
                selected={selection.includes(datastore.id)}
                toggleRow={toggleRow}
                onToggleAutosync={onToggleAutosync}
                onDelete={onDelete}
            />
            ))}
        </Table.Tbody>
        </Table>
    </ScrollArea>
);
