import { Group } from '@mantine/core';

import { DatastoresMetadata } from '@/features/integration/components/DatastoresMetadata.tsx';

export const MetaPage = () => {
    return (
        <div>
            <Group wrap="wrap">
                <DatastoresMetadata/>
            </Group>
        </div>
    );
};
