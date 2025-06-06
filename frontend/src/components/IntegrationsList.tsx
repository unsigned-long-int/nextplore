import { useState, useEffect } from 'react';
import { cibPostgresql } from '@coreui/icons';
import { useMantineTheme } from '@mantine/core';
import CIcon from '@coreui/icons-react';
import cx from 'clsx';
import { 
  Checkbox, 
  Group, 
  ScrollArea, 
  Table, 
  Text 
} from '@mantine/core';
import {
  IconBrandSnowflake,
  IconSql,
  IconBrandMysql,
} from '@tabler/icons-react';

import classes from '../styles/IntegrationsList.module.css';
import { useIntegrations } from '../hooks/useIntegrations';
import type { IntegrationProfile } from '../interface/integration_profile';


export const INTEGRATION_ICONS = [
  {
    key: 'snowflake',
    icon: (theme: any) => <IconBrandSnowflake size={16} color={theme.colors.blue[6]} stroke={1.5} />,
  },
  {
    key: 'sqlserver',
    icon: (theme: any) => <IconSql size={16} color={theme.colors.pink[6]} stroke={1.5} />,
  },
  {
    key: 'postgresql',
    icon: () => <CIcon icon={cibPostgresql} style={{ width: 16, height: 16 }} />,
  },
  {
    key: 'mysql',
    icon: (theme: any) => <IconBrandMysql size={16} color={theme.colors.violet[6]} stroke={1.5} />,
  },
];


export const IntegrationsList = () => {
  const theme = useMantineTheme();
  const { fetchIntegrations } = useIntegrations();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [integrations, setIntegrations] = useState<IntegrationProfile[]>([])
  const [selection, setSelection] = useState(['1']);

  useEffect(() => {
    const getIntegrations = async () => {
      try {
        const integrations_data = await fetchIntegrations();
        setIntegrations(integrations_data);
      } catch (e) {
        setError('Failed to load integrations ' + e);
      } finally {
        setLoading(false);
      }
    };
    getIntegrations();
  }, []);


  if (loading) return <Text>Getting integrations data...</Text>;
  if (error) return <Text c="red">{error}</Text>;
  if (!integrations) return <Text>No integrations data available.</Text>;

  const toggleRow = (id: string) =>
    setSelection((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    );
  const toggleAll = () =>
    setSelection((current) => (current.length === integrations.length ? [] : integrations.map((integration) => integration.id)));

  const getIntegrationIcon = (service_type: string) => {
    const match = INTEGRATION_ICONS.find((entry) => entry.key === service_type.toLowerCase());
    return match ? match.icon(theme) : null;
  };
  const rows = integrations.map((integration) => {
    const selected = selection.includes(integration.id);
    return (
      <Table.Tr key={integration.id} className={cx({ [classes.rowSelected]: selected })}>
        <Table.Td>
          <Checkbox checked={selection.includes(integration.id)} onChange={() => toggleRow(integration.id)} />
        </Table.Td>
        <Table.Td>
          <Group gap="sm">
            {getIntegrationIcon(integration.service_type)}
            <Text size="sm" fw={500}>
              {integration.service_type}
            </Text>
          </Group>
        </Table.Td>
        <Table.Td>{integration.connection_name}</Table.Td>
        <Table.Td>{integration.database_name}</Table.Td>
        <Table.Td>{integration.auth_method}</Table.Td>
      </Table.Tr>
    );
  });

  return (
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
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>{rows}</Table.Tbody>
      </Table>
    </ScrollArea>
  );
}