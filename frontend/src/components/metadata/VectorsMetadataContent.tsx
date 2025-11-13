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
import { useEffect, useState } from 'react';
import { useVectorProfiles } from '../../hooks/useVectorProfiles';
import classes from '../../styles/VectorsMetadata.module.css';
import { LoadingOverlay } from '../loading_overlay/LoadingOverlay';
import type { VectorProfileResponse } from '../../interface/vector/vector-profile-response.interface';

interface ThProps {
    children: React.ReactNode;
    reversed: boolean;
    sorted: boolean;
    onSort: () => void;
}

function Th({ children, reversed, sorted, onSort }: ThProps) {
    const IconComponent = sorted ? (reversed ? IconChevronUp : IconChevronDown) : IconSelector;
    return (
        <Table.Th className={classes.th}>
            <UnstyledButton onClick={onSort} className={classes.control}>
                <Group justify="space-between">
                    <Text fw={500} fz="sm">{children}</Text>
                    <Center className={classes.icon}>
                        <IconComponent size={16} stroke={1.5} />
                    </Center>
                </Group>
            </UnstyledButton>
        </Table.Th>
    );
}

function filterData(data: VectorProfileResponse[], search: string) {
    const query = search.toLowerCase().trim();
    if (!query) return data;
    if (data.length === 0) return data;

    const keys = Object.keys(data[0]) as Array<keyof VectorProfileResponse>;
    return data.filter((item) =>
        keys.some((k) => {
            const v = item[k];
            return typeof v === 'string' && v.toLowerCase().includes(query);
        }),
    );
}

function sortData(
    data: VectorProfileResponse[],
    payload: { sortBy: keyof VectorProfileResponse | null; reversed: boolean; search: string }
) {
    const { sortBy, reversed, search } = payload;
    const base = [...data];

    if (sortBy) {
        base.sort((a, b) => {
            const av = a[sortBy];
            const bv = b[sortBy];
            const as = typeof av === 'string' ? av : String(av ?? '');
            const bs = typeof bv === 'string' ? bv : String(bv ?? '');
            return reversed ? bs.localeCompare(as) : as.localeCompare(bs);
        });
    }

    return filterData(base, search);
}

type Props = { integration_id: string };

export const VectorsMetadataContent: React.FC<Props> = ({ integration_id }) => {
      const { fetchVectorProfiles } = useVectorProfiles();
      const [loading, setLoading] = useState<boolean>(true);
      const [error, setError] = useState<string | null>(null);
      const [vectors, setVectors] = useState<VectorProfileResponse[]>([]);
      const [search, setSearch] = useState('');
      const [sortedData, setSortedData] = useState<VectorProfileResponse[]>([]);
      const [sortBy, setSortBy] = useState<keyof VectorProfileResponse | null>(null);
      const [reverseSortDirection, setReverseSortDirection] = useState(false);

      useEffect(() => {
          let canceled = false;
          const getVectorMetadata = async () => {
          setLoading(true);
          setError(null);
          try {
              const vectorsMetadata = await fetchVectorProfiles(integration_id);
              if (!canceled) {
                  setVectors(vectorsMetadata);
                  setSortedData(vectorsMetadata);
              }
          } catch (e) {
              if (!canceled) setError('Failed to load vectors metadata ' + (e as Error).message);
          } finally {
              if (!canceled) setLoading(false);
          }
          };
    getVectorMetadata();
    return () => { canceled = true; };
  }, [integration_id, fetchVectorProfiles]);

  if (loading) return <LoadingOverlay loadingText="Getting integrations data..." />;
  if (error) return <Text c="red">{error}</Text>;
  if (!vectors || vectors.length === 0) return <Text>No vectors data available.</Text>;

  const setSorting = (field: keyof VectorProfileResponse) => {
    const reversed = field === sortBy ? !reverseSortDirection : false;
    setReverseSortDirection(reversed);
    setSortBy(field);
    setSortedData(sortData(vectors, { sortBy: field, reversed, search }));
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = event.currentTarget;
    setSearch(value);
    setSortedData(sortData(vectors, { sortBy, reversed: reverseSortDirection, search: value }));
  };

  const rows = sortedData.map((row) => (
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
        placeholder="Search by any field"
        mb="md"
        leftSection={<IconSearch size={16} stroke={1.5} />}
        value={search}
        onChange={handleSearchChange}
      />
      <Table horizontalSpacing="md" verticalSpacing="xs" miw={700} layout="fixed">
        <Table.Thead>
          <Table.Tr>
            <Th sorted={sortBy === 'integration_id'} reversed={reverseSortDirection} onSort={() => setSorting('integration_id')}>
              Integration ID
            </Th>
            <Th sorted={sortBy === 'schema_name'} reversed={reverseSortDirection} onSort={() => setSorting('schema_name')}>
              Schema Name
            </Th>
            <Th sorted={sortBy === 'table_name'} reversed={reverseSortDirection} onSort={() => setSorting('table_name')}>
              Table Name
            </Th>
            <Th sorted={sortBy === 'table_meta'} reversed={reverseSortDirection} onSort={() => setSorting('table_meta')}>
              Table Meta
            </Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.length > 0 ? (
            rows
          ) : (
            <Table.Tr>
              <Table.Td colSpan={4}>
                <Text fw={500} ta="center">
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
