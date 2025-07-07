import { Group } from '@mantine/core';
import { IntegrationsMetadataContentNavigator } from '../components/metadata/IntegrationsMetadataContentNavigator';

export const MetadataPage = () => {
    return (
    <div>
         <Group wrap="wrap">
            <IntegrationsMetadataContentNavigator/>
        </Group>
    </div>
    )
};
