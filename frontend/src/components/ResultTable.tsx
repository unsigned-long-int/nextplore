import {
  Table,
  ScrollArea,
  TextInput,
  Group,
  Pagination,
  Paper,
  Text,
} from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

export const ResultTable = ({ data }: { data: any[] }) => {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const headers = useMemo(() => (data.length ? Object.keys(data[0]) : []), [data]);

  const filtered = useMemo(() => {
    if (!query) return data;
    return data.filter((row) =>
      Object.values(row).some((val) =>
        String(val).toLowerCase().includes(query.toLowerCase())
      )
    );
  }, [query, data]);

  const totalPages = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  if (!data || data.length === 0) {
    return <Text c="dimmed">No data available.</Text>;
  }

  return (
    <Paper withBorder p="md" radius="md">
      <Group justify="space-between" mb="sm">
        <TextInput
          placeholder="Search table..."
          value={query}
          onChange={(e) => {
            setQuery(e.currentTarget.value);
            setPage(1);
          }}
          leftSection={<IconSearch size={16} />}
        />
        <Pagination page={page} onChange={setPage} total={totalPages} size="sm" />
      </Group>

      <ScrollArea>
        <Table striped highlightOnHover withColumnBorders>
          <thead>
            <tr>{headers.map((h) => <th key={h}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {paginated.map((row, i) => (
              <tr key={i}>
                {headers.map((h) => <td key={h}>{row[h]}</td>)}
              </tr>
            ))}
          </tbody>
        </Table>
      </ScrollArea>
    </Paper>
  );
};