import { Checkbox, Group, Switch, Table, Text } from '@mantine/core';
import cx from 'clsx';

import classes from '@/styles/IntegrationsList.module.css';
import { DatastoreActionsMenu } from '@/features/integration/components/DatastoreActionsMenu.tsx';
import { DatastoreIcon } from '@/features/integration/components/DatastoreIcon.tsx';
import type { DataStoreProfile } from '@/shared/api/services/integration/types.gen';


interface Props {
    datastore: DataStoreProfile,
    index: number,
    selected: boolean,
    toggleRow: (id: string) => void,
    onToggleAutosync: (index: number, enabled: boolean) => void;
    onDelete: (id: string) => void
}


export const DatastoreRow = ({
    datastore,
    index,
    selected,
    toggleRow,
    onToggleAutosync,
    onDelete
}: Props) => {
    return (
        <Table.Tr key={datastore.id} className={cx({ [classes.rowSelected]: selected })}>
            <Table.Td>
                <Checkbox checked={selected} onChange={() => toggleRow(datastore.id)} />
            </Table.Td>
            <Table.Td>
                <Group gap="sm">
                    <DatastoreIcon serviceType={datastore.db} />
                    <Text size="sm" fw={500}>{datastore.db}</Text>
                </Group>
            </Table.Td>
            <Table.Td>{datastore.auth}</Table.Td>
            <Table.Td>{datastore.cloud}</Table.Td>
            <Table.Td>{datastore.connection_name}</Table.Td>
            <Table.Td>{datastore.database_name}</Table.Td>
            <Table.Td>{datastore.host}</Table.Td>
            <Table.Td>{datastore.port}</Table.Td>
            <Table.Td>
            <Switch
                checked={datastore.autosync_on}
                onLabel="ON"
                offLabel="OFF"
                className={classes.switch}
                size="lg"
                onChange={(e) => onToggleAutosync(index, e.currentTarget.checked)}
            />
            </Table.Td>
            <Table.Td>
            <DatastoreActionsMenu onDelete={() => onDelete(datastore.id)} />
            </Table.Td>
        </Table.Tr>
    )
};