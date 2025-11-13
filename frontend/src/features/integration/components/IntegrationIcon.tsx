import { cibPostgresql } from '@coreui/icons';
import { CIcon } from '@coreui/icons-react';
import { useMantineTheme } from '@mantine/core';
import { IconBrandMysql, IconBrandSnowflake, IconSql } from '@tabler/icons-react';
import type { JSX } from 'react';

import { DB } from '@/shared/api/services/integration/types.gen.ts'


export const IntegrationIcon = ({ serviceType }: { serviceType: DB}) => {
    const theme = useMantineTheme();
    const icons: Record<string, JSX.Element> = {
        snowflake: <IconBrandSnowflake size={16} color={theme.colors.blue[6]} stroke={1.5} />,
        sqlserver: <IconSql size={16} color={theme.colors.pink[6]} stroke={1.5} />,
        postgresql: <CIcon icon={cibPostgresql} style={{ width: 16, height: 16 }} />,
        mysql: <IconBrandMysql size={16} color={theme.colors.violet[6]} stroke={1.5} />
    };
    return icons[serviceType.toLowerCase()] ?? null;
};
