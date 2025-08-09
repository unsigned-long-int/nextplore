import {
    Center,
    Group,
    ScrollArea,
    Table,
    Text,
    TextInput,
    UnstyledButton,
    keys
} from '@mantine/core';
import { IconChevronDown, IconChevronUp, IconSearch, IconSelector } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useVectorProfiles } from '../../hooks/useVectorProfiles';
import type { VectorProfileRequest } from '../../interface/vector-profile-request.interface';
import type { VectorProfile } from '../../interface/vector-profile.interface';
import classes from '../../styles/VectorsMetadata.module.css';
import { LoadingOverlay } from '../loading_overlay/LoadingOverlay';


interface ThProps {
    children: React.ReactNode;
    reversed: boolean;
    sorted: boolean;
    onSort: () => void;
}

function Th({ children, reversed, sorted, onSort }: ThProps) {
const Icon = sorted ? (reversed ? IconChevronUp : IconChevronDown) : IconSelector;
return (
    <Table.Th className={classes.th}>
    <UnstyledButton onClick={onSort} className={classes.control}>
        <Group justify="space-between">
        <Text fw={500} fz="sm">
            {children}
        </Text>
        <Center className={classes.icon}>
            <Icon size={16} stroke={1.5} />
        </Center>
        </Group>
    </UnstyledButton>
    </Table.Th>
    );
}


function filterData(data: VectorProfile[], search: string) {
    const query = search.toLowerCase().trim();
    return data.filter((item) =>
      keys(data[0]).some((key) => item[key].toLowerCase().includes(query))
    );
}

function sortData(
    data: VectorProfile[],
    payload: { sortBy: keyof VectorProfile | null; reversed: boolean; search: string }
  ) {
    const { sortBy } = payload;
  
    if (!sortBy) {
      return filterData(data, payload.search);
    }
  
    return filterData(
      [...data].sort((a, b) => {
        if (payload.reversed) {
          return b[sortBy].localeCompare(a[sortBy]);
        }
  
        return a[sortBy].localeCompare(b[sortBy]);
      }),
      payload.search
    );
}

export const VectorsMetadataContent = ({ vector_profile_request }: { vector_profile_request: VectorProfileRequest }) => {
    const { fetchVectorProfiles } = useVectorProfiles();
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [vectors, setVectors] = useState<VectorProfile[]>([]);
    const [search, setSearch] = useState('');
    const [sortedData, setSortedData] = useState<VectorProfile[]>([]);
    const [sortBy, setSortBy] = useState<keyof VectorProfile | null>(null);
    const [reverseSortDirection, setReverseSortDirection] = useState(false);
  

    useEffect(() => {
        const getVectorMetadata = async() => {
        try {
            const vectors_metadata = await fetchVectorProfiles(vector_profile_request);
            setVectors(vectors_metadata);
            setSortedData(vectors_metadata)
        } catch (e) {
            setError('Failed to load vectors metadata ' + e);
        } finally {
            setLoading(false);
        }
    };
    getVectorMetadata();
    }, [vector_profile_request]);

    if (loading) return <LoadingOverlay loadingText="Getting integrations data..."/>;
    if (error) return <Text c="red">{error}</Text>;
    if (!vectors || vectors.length == 0) return <Text>No vectors data available.</Text>;

    const setSorting = (field: keyof VectorProfile) => {
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
        <Table.Tr key={row.schema_name + '.' + row.table_name}>
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
            <Table.Tbody>
              <Table.Tr>
                <Th
                  sorted={sortBy === 'integration_id'}
                  reversed={reverseSortDirection}
                  onSort={() => setSorting('integration_id')}
                >
                    Integration ID
                </Th>
                <Th
                  sorted={sortBy === 'schema_name'}
                  reversed={reverseSortDirection}
                  onSort={() => setSorting('schema_name')}
                >
                  Schema Name
                </Th>
                <Th
                  sorted={sortBy === 'table_name'}
                  reversed={reverseSortDirection}
                  onSort={() => setSorting('table_name')}
                >
                  Table Name
                </Th>
                <Th
                  sorted={sortBy === 'table_meta'}
                  reversed={reverseSortDirection}
                  onSort={() => setSorting('table_meta')}
                >
                  Table Meta
                </Th>
              </Table.Tr>
            </Table.Tbody>
            <Table.Tbody>
              {rows.length > 0 ? (
                rows
              ) : (
                <Table.Tr>
                  <Table.Td colSpan={vectors[0] ? Object.keys(vectors[0]).length : 1}>
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
}