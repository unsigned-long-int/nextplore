import { Group } from '@mantine/core';

import { IntegrationsMetadata } from '@/features/integration/components/IntegrationsMetadata';

export const MetaPage = () => {
    return (
        <div>
            <Group wrap="wrap">
                <IntegrationsMetadata/>
            </Group>
        </div>
    );
};
