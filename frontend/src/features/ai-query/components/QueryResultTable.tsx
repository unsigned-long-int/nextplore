import {
    Box,
    Button,
    Chip,
    InputAdornment,
    Paper,
    TextField,
    Typography,
} from '@mui/material';
import {
    Download as DownloadIcon,
    Search as SearchIcon,
    TableChart as TableChartIcon,
} from '@mui/icons-material';
import type { GridColDef } from '@mui/x-data-grid';
import { DataGrid } from '@mui/x-data-grid';
import ExcelJS from 'exceljs';
import { saveAs } from 'file-saver';
import { useMemo, useState } from 'react';

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

    const exportToCSV = async () => {
        if (filteredRows.length === 0) return;
        const workbook = new ExcelJS.Workbook();
        const worksheet = workbook.addWorksheet('Results');
        worksheet.columns = Object.keys(filteredRows[0]).map((key) => ({ header: key, key }));
        filteredRows.forEach((row) => worksheet.addRow(row));
        const csvBuffer = await workbook.csv.writeBuffer();
        const blob = new Blob([csvBuffer], { type: 'text/csv;charset=utf-8;' });
        saveAs(blob, 'results.csv');
    };

    if (!data || data.length === 0) {
        return (
            <Typography sx={{ color: 'rgba(255,255,255,0.25)', fontStyle: 'italic', fontSize: '0.875rem' }}>
                No data available.
            </Typography>
        );
    }

    return (
        <Paper
            elevation={0}
            sx={{
                height: 'clamp(360px, 70vh, 720px)',
                display: 'flex',
                flexDirection: 'column',
                background: 'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
                border: '1px solid rgba(168,85,247,0.15)',
                borderRadius: '16px',
                overflow: 'hidden',
                boxShadow: '0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(168,85,247,0.05)',
            }}
        >
            <Box
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    px: 2.5,
                    py: 1.75,
                    borderBottom: '1px solid rgba(168,85,247,0.1)',
                    background: 'rgba(13,15,30,0.8)',
                    gap: 2,
                    flexWrap: 'wrap',
                }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                    <TableChartIcon sx={{ fontSize: 14, color: '#a855f7' }} />
                    <Typography
                        variant="caption"
                        sx={{
                            color: '#a855f7',
                            fontWeight: 700,
                            letterSpacing: '0.1em',
                            textTransform: 'uppercase',
                            fontSize: '0.65rem',
                        }}
                    >
                        Query Results
                    </Typography>
                    <Chip
                        label={`${filteredRows.length} rows`}
                        size="small"
                        sx={{
                            background: 'rgba(168,85,247,0.1)',
                            color: 'rgba(196,132,252,0.8)',
                            border: '1px solid rgba(168,85,247,0.2)',
                            borderRadius: '6px',
                            fontSize: '0.65rem',
                            fontWeight: 600,
                            height: 20,
                            '& .MuiChip-label': { px: 1 },
                        }}
                    />
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <TextField
                        size="small"
                        placeholder="Search..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        InputProps={{
                            startAdornment: (
                                <InputAdornment position="start">
                                    <SearchIcon sx={{ fontSize: 15, color: 'rgba(168,85,247,0.4)' }} />
                                </InputAdornment>
                            ),
                        }}
                        sx={{
                            width: 240,
                            '& .MuiOutlinedInput-root': {
                                background: 'rgba(168,85,247,0.05)',
                                borderRadius: '9px',
                                color: '#e2e8f0',
                                fontSize: '0.82rem',
                                height: 34,
                                '& fieldset': { borderColor: 'rgba(168,85,247,0.15)' },
                                '&:hover fieldset': { borderColor: 'rgba(168,85,247,0.3)' },
                                '&.Mui-focused fieldset': {
                                    borderColor: 'rgba(168,85,247,0.6)',
                                    borderWidth: '1px',
                                },
                            },
                            '& input::placeholder': { color: 'rgba(255,255,255,0.18)' },
                        }}
                    />

                    <Button
                        size="small"
                        startIcon={<DownloadIcon sx={{ fontSize: '14px !important' }} />}
                        onClick={exportToCSV}
                        sx={{
                            background: 'rgba(168,85,247,0.1)',
                            color: 'rgba(196,132,252,0.85)',
                            border: '1px solid rgba(168,85,247,0.2)',
                            borderRadius: '9px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            textTransform: 'none',
                            px: 1.75,
                            height: 34,
                            letterSpacing: '0.02em',
                            transition: 'all 0.15s ease',
                            '&:hover': {
                                background: 'rgba(168,85,247,0.2)',
                                borderColor: 'rgba(168,85,247,0.45)',
                                color: '#c084fc',
                                boxShadow: '0 0 14px rgba(168,85,247,0.25)',
                                transform: 'translateY(-1px)',
                            },
                        }}
                    >
                        Export CSV
                    </Button>
                </Box>
            </Box>

            <Box sx={{ flex: 1, minHeight: 0 }}>
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
                        border: 'none',
                        color: '#cbd5e1',
                        bgcolor: 'transparent',
                        '--DataGrid-rowBorderColor': 'rgba(168,85,247,0.07)',
                        '--DataGrid-containerBackground': '#0c0e1f',
                        '--DataGrid-headerBackground': '#0c0e1f',

                        '& .MuiDataGrid-columnHeaders': {
                            backgroundColor: '#0c0e1f',
                            borderBottom: '1px solid rgba(168,85,247,0.12)',
                        },
                        '& .MuiDataGrid-columnHeader': { backgroundColor: '#0c0e1f' },
                        '& .MuiDataGrid-columnHeaderTitle': {
                            color: '#7c3aed',
                            fontWeight: 700,
                            fontSize: '0.7rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                        },
                        '& .MuiDataGrid-cell': {
                            borderColor: 'rgba(168,85,247,0.06)',
                            fontSize: '0.83rem',
                            color: '#cbd5e1',
                        },
                        '& .MuiDataGrid-row:hover': {
                            backgroundColor: 'rgba(168,85,247,0.05)',
                        },
                        '& .MuiDataGrid-row.Mui-selected': {
                            backgroundColor: 'rgba(168,85,247,0.09)',
                            '&:hover': { backgroundColor: 'rgba(168,85,247,0.13)' },
                        },
                        '& .MuiDataGrid-footerContainer': {
                            backgroundColor: '#0b0d1d',
                            borderTop: '1px solid rgba(168,85,247,0.1)',
                        },
                        '& .MuiTablePagination-root, & .MuiTablePagination-toolbar, & .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                            color: '#64748b',
                            fontSize: '0.75rem',
                        },
                        '& .MuiSvgIcon-root': { color: '#4c1d95' },
                        '& .MuiDataGrid-columnSeparator': { color: 'rgba(168,85,247,0.08)' },
                        '& .MuiDataGrid-menuIconButton': { color: '#6d28d9' },
                        '& .MuiDataGrid-selectedRowCount': { color: '#6d28d9' },
                        '& .MuiDataGrid-virtualScroller': {
                            scrollbarColor: '#2e1065 transparent',
                            scrollbarWidth: 'thin',
                            '&::-webkit-scrollbar': { width: 5, height: 5 },
                            '&::-webkit-scrollbar-thumb': {
                                background: 'rgba(168,85,247,0.25)',
                                borderRadius: 3,
                            },
                            '&::-webkit-scrollbar-track': { background: 'transparent' },
                        },
                        '& .MuiDataGrid-sortIcon': { color: '#a855f7' },
                        '& .MuiDataGrid-filterIcon': { color: '#a855f7' },
                    }}
                />
            </Box>
        </Paper>
    );
};