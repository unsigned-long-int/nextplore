import { Button, Group, Paper, Text, TextInput } from '@mantine/core';
import type { GridColDef } from '@mui/x-data-grid';
import { DataGrid } from '@mui/x-data-grid';
import { IconDownload, IconSearch } from '@tabler/icons-react';
import { saveAs } from 'file-saver';
import { useMemo, useState } from 'react';
import { utils } from 'xlsx';

export const QueryResultTable = ({ data }: { data: any[] }) => {
    const [query, setQuery] = useState('');

    const columns: GridColDef[] = useMemo(() => {
        if (!data?.length) return [];
        return Object.keys(data[0]).map((key) => ({
            field: key,
            headerName: key,
            flex: 1,
            minWidth: 120,
            sortable: true,
        }));
    }, [data]);

    const filteredRows = useMemo(() => {
        if (!query) return data;
        return data.filter((row) =>
        Object.values(row).some((val) =>
            String(val).toLowerCase().includes(query.toLowerCase())
        )
        );
    }, [query, data]);

    const rows = filteredRows.map((row, index) => ({ id: index, ...row }));

    const exportToCSV = () => {
        const worksheet = utils.json_to_sheet(filteredRows);
        const csv = utils.sheet_to_csv(worksheet);
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        saveAs(blob, 'results.csv');
    };

    if (!data || data.length === 0) {
        return <Text c='dimmed'>No data available.</Text>;
    }

    return (
        <Paper
        withBorder
        p='md'
        radius='md'
        style={{
            height: 'clamp(360px, 70vh, 720px)',
            display: 'flex',
            flexDirection: 'column',
            background: '#0b0f19',
        }}
        >
            <Group justify='space-between' mb='sm'>
                <TextInput
                    placeholder='Search...'
                    value={query}
                    onChange={(e) => setQuery(e.currentTarget.value)}
                    leftSection={<IconSearch size={16} />}
                    style={{ width: 280 }}
                />
                <Button
                    variant='light'
                    size='xs'
                    onClick={exportToCSV}
                    leftSection={<IconDownload size={14} />}
                >
                    Export CSV
                </Button>
            </Group>

            <div style={{ flex: 1, minHeight: 0 }}>
                <DataGrid
                    rows={rows}
                    columns={columns}
                    disableRowSelectionOnClick
                    pageSizeOptions={[5, 10, 25, 50]}
                    initialState={{
                        pagination: { paginationModel: { pageSize: 10, page: 0 } },
                    }}
                    rowHeight={40}
                    columnHeaderHeight={44}
                    style={{ height: '100%', width: '100%' }}
                    sx={{
                        color: '#e5e7eb',
                        bgcolor: '#0b0f19',
                        backgroundColor: '#0b0f19',
                        borderColor: '#1e293b',
                        '--DataGrid-rowBorderColor': '#1e293b',

                        '& .MuiDataGrid-columnHeaders': {
                          backgroundColor: '#111827',
                          color: '#e5e7eb',
                          borderBottom: '1px solid #1f2937',
                          fontWeight: 600,
                        },
                        '& .MuiDataGrid-columnHeader': {
                          backgroundColor: '#111827',
                          color: '#e5e7eb',
                        },
                        '& .MuiDataGrid-columnHeaderTitle': {
                          color: '#e5e7eb',
                        },

                        '& .MuiDataGrid-cell': { borderColor: '#1e293b' },
                        '& .MuiDataGrid-row:hover': { backgroundColor: '#0f172a' },

                        '& .MuiDataGrid-footerContainer': {
                          backgroundColor: '#0b1220',
                          borderTop: '1px solid #1f2937',
                          color: '#cbd5e1',
                        },
                        '& .MuiSvgIcon-root': { color: '#94a3b8' },
                        '& .MuiTablePagination-root, & .MuiTablePagination-toolbar, & .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                          color: '#cbd5e1',
                        },
                        '& .MuiDataGrid-columnSeparator': { color: '#334155' },
                        '& .MuiDataGrid-menuIconButton': { color: '#94a3b8' },
                        '& .MuiDataGrid-selectedRowCount': { color: '#94a3b8' },
                        '& .MuiDataGrid-virtualScroller': { scrollbarColor: '#334155 #0b0f19' },

                        '--DataGrid-containerBackground': '#111827',
                        '--DataGrid-headerBackground': '#111827',
                    }}
                />
            </div>
        </Paper>
    );
};
