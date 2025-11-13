import { Box, Group, Text } from '@mantine/core';
import { IconListSearch } from '@tabler/icons-react';
import cx from 'clsx';
import { useState } from 'react';

import { useIntegrationProfiles } from '@/features/integration/hooks/useIntegrationProfiles';
import classes from '@/styles/IntegrationsMetadataContentNavigator.module.css';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';
import { VectorsMetadata } from '@/features/vector/components/VectorsMetadata';


export const IntegrationsMetadata = () => {
    const { isPending, isError, error, data } = useIntegrationProfiles();
    const [active, setActive] = useState(0);


    if (isPending) return <LoadingOverlay loadingText="Getting integrations data..."/>;
    if (isError) return <Text c="red">{error.message}</Text>;
    if (!data || data.length == 0) return <Text>No integrations data available.</Text>;

    const items = data.map((item, index) => (
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
                Vectors for: {data[active].connection_name}
            </Text>
            <VectorsMetadata
                integration_id={data[active].id}
            />
        </div>
    </div>
    );
}