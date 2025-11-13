import { Checkbox, Group, Switch, Table, Text } from '@mantine/core';
import cx from 'clsx';
import classes from '../../styles/IntegrationsList.module.css';
import { IntegrationActionsMenu } from './IntegrationActionMenu';
import { IntegrationIcon } from './IntegrationIcon';
import type { IntegrationProfile } from '../../interface/integration/integration-profile.interface';



interface Props {
    integration: IntegrationProfile,
    index: number,
    selected: boolean,
    toggleRow: (id: string) => void,
    onToggleAutosync: (index: number, enabled: boolean) => void;
    onDelete: (id: string) => void
}

export const IntegrationRow = ({
    integration, 
    index,
    selected, 
    toggleRow,
    onToggleAutosync,
    onDelete
}: Props) => {
    return (
        <Table.Tr key={integration.id} className={cx({ [classes.rowSelected]: selected })}>
            <Table.Td>
                <Checkbox checked={selected} onChange={() => toggleRow(integration.id)} />
            </Table.Td>
            <Table.Td>
                <Group gap="sm">
                    <IntegrationIcon serviceType={integration.db} />
                    <Text size="sm" fw={500}>{integration.db}</Text>
                </Group>
            </Table.Td>
            <Table.Td>{integration.auth}</Table.Td>
            <Table.Td>{integration.cloud}</Table.Td>
            <Table.Td>{integration.connection_name}</Table.Td>
            <Table.Td>{integration.database_name}</Table.Td>
            <Table.Td>{integration.host}</Table.Td>
            <Table.Td>{integration.port}</Table.Td>
            <Table.Td>
            <Switch
                checked={integration.autosync_on}
                onLabel="ON"
                offLabel="OFF"
                className={classes.switch}
                size="lg"
                onChange={(e) => onToggleAutosync(index, e.currentTarget.checked)}
            />
            </Table.Td>
            <Table.Td>
            <IntegrationActionsMenu onDelete={() => onDelete(integration.id)} />
            </Table.Td>
        </Table.Tr>
    )
};