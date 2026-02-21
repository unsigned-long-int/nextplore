import {
  Center,
  Group,
  ScrollArea,
  Table,
  Text,
  TextInput,
  UnstyledButton,
} from '@mantine/core';
import { IconChevronDown, IconChevronUp, IconSearch, IconSelector } from '@tabler/icons-react';
import {useMemo, useState} from 'react';

import { useVectorProfiles } from '@/features/vector/hooks/useVectorProfiles';
import classes from '@/styles/VectorsMetadata.module.css';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';
import type { VectorProfileResponse } from '@/shared/api/services/vector/types.gen';

interface VectorTableProps {
    children: React.ReactNode;
    reversed: boolean;
    sorted: boolean;
    onSort: () => void;
}

const VectorTable = ({ children, reversed, sorted, onSort }: VectorTableProps) => {
    const IconComponent = sorted ? (reversed ? IconChevronUp : IconChevronDown) : IconSelector;
    return (
        <Table.Th className={classes.th}>
            <UnstyledButton onClick={onSort} className={classes.control}>
                <Group justify='space-between'>
                    <Text fw={500} fz='sm'>{children}</Text>
                    <Center className={classes.icon}>
                        <IconComponent size={16} stroke={1.5} />
                    </Center>
                </Group>
            </UnstyledButton>
        </Table.Th>
    )
}


const getString = (v: unknown) => {
    return typeof v === 'string' ? v : v == null ? '' : String(v);
};

const filterData = (data: VectorProfileResponse[], search: string) => {
    const query = search.toLowerCase().trim();
    if (!query) return data;
    if (data.length === 0) return data;

    const keys = Object.keys(data[0]) as Array<keyof VectorProfileResponse>;
    return data.filter((item) =>
        keys.some((k) => {
            const v = item[k];
            return getString(v).toLowerCase().includes(query);
        }),
    );
};


const sortData = (
    data: VectorProfileResponse[],
    payload: { sortBy: keyof VectorProfileResponse | null; reversed: boolean; search: string }
) => {
    const { sortBy, reversed, search } = payload;
    const base = [...data];

    if (sortBy) {
        base.sort((a, b) => {
            const av = a[sortBy];
            const bv = b[sortBy];
            return reversed ? getString(bv).localeCompare(av) : getString(av).localeCompare(bv);
        });
    }

    return filterData(base, search);
}

type VectorMetaProps = {
    integration_id: string
};


export const VectorsMetadata: React.FC<VectorMetaProps> = ({ integration_id }) => {
    const { isPending, isError, data, error } = useVectorProfiles(integration_id);
    const [search, setSearch] = useState<string>('');
    const [sortBy, setSortBy] = useState<keyof VectorProfileResponse | null>(null);
    const [reverseSortDirection, setReverseSortDirection] = useState<boolean>(false);
    const displayData = useMemo(
        () => sortData(data ?? [], {sortBy, reversed: reverseSortDirection, search}),
        [data, sortBy, reverseSortDirection, search]
    )


    if (isPending) return <LoadingOverlay loadingText='Getting integrations data...' />;
    if (isError) return <Text c='red'>{error.message}</Text>;
    if (!data || data.length === 0) return <Text>No vectors data available.</Text>;



    const setSorting = (field: keyof VectorProfileResponse) => {
        const reversed = field === sortBy ? !reverseSortDirection : false;
        setReverseSortDirection(reversed);
        setSortBy(field);
    };

    const rows = displayData.map((row) => (
        <Table.Tr key={`${row.schema_name}.${row.table_name}`}>
            <Table.Td>{row.integration_id}</Table.Td>
            <Table.Td>{row.schema_name}</Table.Td>
            <Table.Td>{row.table_name}</Table.Td>
            <Table.Td>{row.table_meta}</Table.Td>
        </Table.Tr>
    ));

    return (
        <ScrollArea>
            <TextInput
                placeholder='Search by any field'
                mb='md'
                leftSection={<IconSearch size={16} stroke={1.5} />}
                value={search}
                onChange={(e) => setSearch(e.currentTarget.value)}
            />
            <Table horizontalSpacing='md' verticalSpacing='xs' miw={700} layout='fixed'>
                <Table.Thead>
                    <Table.Tr>
                        <VectorTable
                            sorted={sortBy === 'integration_id'}
                            reversed={reverseSortDirection}
                            onSort={() => setSorting('integration_id')}
                        >
                            Integration ID
                        </VectorTable>
                        <VectorTable
                            sorted={sortBy === 'schema_name'}
                            reversed={reverseSortDirection}
                            onSort={() => setSorting('schema_name')}
                        >
                            Schema Name
                        </VectorTable>
                        <VectorTable
                            sorted={sortBy === 'table_name'}
                            reversed={reverseSortDirection}
                            onSort={() => setSorting('table_name')}
                        >
                            Table Name
                        </VectorTable>
                        <VectorTable
                            sorted={sortBy === 'table_meta'}
                            reversed={reverseSortDirection}
                            onSort={() => setSorting('table_meta')}
                        >
                            Table Meta
                        </VectorTable>
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                    {rows.length > 0 ? (
                        rows
                    ) : (
                        <Table.Tr>
                            <Table.Td colSpan={4}>
                                <Text fw={500} ta='center'>
                                    Nothing found
                                </Text>
                            </Table.Td>
                        </Table.Tr>
                        )}
                </Table.Tbody>
            </Table>
        </ScrollArea>
    );
};
