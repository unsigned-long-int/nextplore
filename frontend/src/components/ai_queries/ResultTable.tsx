import {
    Button,
    Group,
    Pagination,
    Paper,
    ScrollArea,
    Table,
    Text,
    TextInput,
} from '@mantine/core';
import { IconDownload, IconSearch } from '@tabler/icons-react';
import { saveAs } from 'file-saver';
import { useMemo, useState } from 'react';
import * as XLSX from 'xlsx';


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

    const exportToCSV = () => {
        const worksheet = XLSX.utils.json_to_sheet(filtered);
        const csv = XLSX.utils.sheet_to_csv(worksheet);
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        saveAs(blob, 'results.csv');
    };

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
            <Group>
            <Button variant="light" size="xs" onClick={exportToCSV} leftSection={<IconDownload size={14} />}>
                Export CSV
            </Button>
            <Pagination value={page} onChange={setPage} total={totalPages} size="sm" />
            </Group>
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