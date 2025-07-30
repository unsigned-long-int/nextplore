import { Box, Group, Text } from '@mantine/core';
import { IconListSearch } from '@tabler/icons-react';
import cx from 'clsx';
import { useEffect, useState } from 'react';
import { useIntegrations } from '../../hooks/useIntegrations';
import type { IntegrationProfile } from '../../interface/integration-profile.interface';
import classes from '../../styles/IntegrationsMetadataContentNavigator.module.css';
import { VectorsMetadataContent } from './VectorsMetadataContent';


export const IntegrationsMetadataContentNavigator = () => {
    const { fetchIntegrations } = useIntegrations();

    const [active, setActive] = useState(0);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [integrations, setIntegrations] = useState<IntegrationProfile[]>([])
  
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
    if (!integrations || integrations.length == 0) return <Text>No integrations data available.</Text>;

    const items = integrations.map((item, index) => (
        <Box<'a'>
            component="a"
            href={item.id}
            onClick={(event) => {
                event.preventDefault();
                setActive(index);
            }}
            key={item.id}
            className={cx(classes.link, { [classes.linkActive]: active === index })}
            style={{ paddingLeft: `var(--mantine-spacing-md)` }}
        >
        {item.connection_name}
        </Box>
    ));

    return (
        <div className={classes.container}>
            <div className={classes.sidebar}>
                <Group mb="md">
                    <IconListSearch size={18} stroke={1.5} />
                    <Text>Integrations</Text>
                </Group>
                <div className={classes.links}>
                    <div
                    className={classes.indicator}
                    style={{
                        transform: `translateY(calc(${active} * var(--link-height) + var(--indicator-offset)))`,
                    }}
                    />
                    {items}
                </div>
        </div>
        <div className={classes.tableArea}>
            <Text fw={500} mb="sm">
                Vectors for: {integrations[active].connection_name}
            </Text>
            <VectorsMetadataContent 
                key={integrations[active].id}
                vector_profile_request={{ integration_id: integrations[active].id }}
            />
        </div>
    </div>
    );
}