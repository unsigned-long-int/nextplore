import { Box, Typography } from '@mui/material';
import { IconListSearch } from '@tabler/icons-react';
import { useState } from 'react';

import { useDatastoreProfiles } from '@/features/integration/hooks/useDatastoreProfiles.ts';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';
import { VectorsMetadata } from '@/features/vector/components/VectorsMetadata';

const P = {
    border:  'rgba(168,85,247,0.18)',
    soft:    'rgba(168,85,247,0.08)',
    active:  'rgba(168,85,247,0.14)',
    icon:    '#a855f7',
    label:   '#c084fc',
    dim:     'rgba(255,255,255,0.28)',
    text:    '#cbd5e1',
    bg:      'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
};

export const DatastoresMetadata = () => {
    const { isPending, isError, error, data } = useDatastoreProfiles();
    const [active, setActive] = useState(0);

    if (isPending) return <LoadingOverlay loadingText="Getting data stores data…" />;
    if (isError)   return <Typography sx={{ color: '#f87171', fontSize: '0.82rem' }}>{error.message}</Typography>;
    if (!data || data.length === 0) return <Typography sx={{ color: P.dim, fontSize: '0.82rem' }}>No data stores data available.</Typography>;

    return (
        <Box sx={{
            display: 'flex',
            width: '100%',
            minHeight: 480,
            background: P.bg,
            border: `1px solid ${P.border}`,
            borderRadius: '16px',
            overflow: 'hidden',
            boxShadow: '0 8px 32px rgba(0,0,0,0.45), 0 0 0 1px rgba(168,85,247,0.05)',
        }}>

            <Box sx={{
                width: 220,
                flexShrink: 0,
                borderRight: `1px solid ${P.border}`,
                display: 'flex',
                flexDirection: 'column',
            }}>
                <Box sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    px: 2,
                    py: 1.75,
                    borderBottom: `1px solid ${P.border}`,
                    background: 'rgba(168,85,247,0.04)',
                }}>
                    <IconListSearch size={13} color={P.icon} stroke={1.5} />
                    <Typography sx={{
                        color: P.icon,
                        fontSize: '0.62rem',
                        fontWeight: 700,
                        letterSpacing: '0.1em',
                        textTransform: 'uppercase',
                    }}>
                        Integrations
                    </Typography>
                </Box>

                <Box sx={{ flex: 1, py: 1, overflowY: 'auto',
                    scrollbarWidth: 'thin',
                    scrollbarColor: 'rgba(168,85,247,0.2) transparent',
                    '&::-webkit-scrollbar': { width: 4 },
                    '&::-webkit-scrollbar-thumb': { background: 'rgba(168,85,247,0.2)', borderRadius: 2 },
                }}>
                    {data.map((item, index) => {
                        const isActive = active === index;
                        return (
                            <Box
                                key={item.id}
                                component="a"
                                href={item.id}
                                onClick={(e) => { e.preventDefault(); setActive(index); }}
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1.25,
                                    px: 2,
                                    py: 1,
                                    mx: 0.75,
                                    borderRadius: '8px',
                                    textDecoration: 'none',
                                    fontSize: '0.83rem',
                                    fontWeight: isActive ? 600 : 400,
                                    color: isActive ? P.label : P.text,
                                    background: isActive ? P.active : 'transparent',
                                    borderLeft: isActive
                                        ? `2px solid ${P.icon}`
                                        : '2px solid transparent',
                                    transition: 'all 0.15s ease',
                                    cursor: 'pointer',
                                    '&:hover': {
                                        background: P.soft,
                                        color: '#f1f5f9',
                                    },
                                }}
                            >
                                <Box sx={{
                                    width: 6, height: 6,
                                    borderRadius: '50%',
                                    background: isActive ? P.icon : 'rgba(255,255,255,0.15)',
                                    boxShadow: isActive ? `0 0 6px ${P.icon}` : 'none',
                                    flexShrink: 0,
                                    transition: 'all 0.15s ease',
                                }} />
                                <Typography sx={{
                                    fontSize: '0.83rem',
                                    fontWeight: isActive ? 600 : 400,
                                    color: 'inherit',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                }}>
                                    {item.connection_name}
                                </Typography>
                            </Box>
                        );
                    })}
                </Box>
            </Box>

            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                <Box sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.25,
                    px: 2.5,
                    py: 1.75,
                    borderBottom: `1px solid ${P.border}`,
                    background: 'rgba(168,85,247,0.03)',
                }}>
                    <Box sx={{
                        width: 6, height: 6, borderRadius: '50%',
                        background: P.icon,
                        boxShadow: `0 0 8px ${P.icon}`,
                    }} />
                    <Typography sx={{ color: P.dim, fontSize: '0.75rem', fontWeight: 500 }}>
                        Vectors for
                    </Typography>
                    <Typography sx={{
                        color: '#f1f5f9',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                    }}>
                        {data[active].connection_name}
                    </Typography>
                </Box>

                <Box sx={{ flex: 1, p: 2.5, minHeight: 0 }}>
                    <VectorsMetadata datastore_id={data[active].id} />
                </Box>
            </Box>
        </Box>
    );
};