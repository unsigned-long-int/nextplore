import { Box, Grid, Paper, Typography } from '@mui/material';
import { IconDatabase, IconVector } from '@tabler/icons-react';
import { useUserStats } from '@/features/user/hooks/useUserStats';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';

const P = {
    border: 'rgba(168,85,247,0.18)',
    soft:   'rgba(168,85,247,0.08)',
    icon:   '#a855f7',
    label:  '#c084fc',
    dim:    'rgba(255,255,255,0.3)',
};

const STAT_CONFIG = [
    {
        key: 'datastores_number',
        title: 'Data Stores',
        icon: IconDatabase,
        accent: '#a855f7',
        glow: 'rgba(168,85,247,0.25)',
        bg: 'rgba(168,85,247,0.07)',
    },
    {
        key: 'vectors_number',
        title: 'Vectors',
        icon: IconVector,
        accent: '#38bdf8',
        glow: 'rgba(56,189,248,0.2)',
        bg: 'rgba(56,189,248,0.07)',
    },
];

export const UserStats = () => {
    const { isPending, isError, error, data } = useUserStats();

    if (isPending) return <LoadingOverlay loadingText="Getting user stats…" />;
    if (isError) return (
        <Typography sx={{ color: '#f87171', fontSize: '0.82rem' }}>{error.message}</Typography>
    );
    if (!data) return (
        <Typography sx={{ color: P.dim, fontSize: '0.82rem' }}>No stats available.</Typography>
    );

    return (
        <Grid container spacing={2} sx={{ mt: 0.5 }}>
            {STAT_CONFIG.map(({ key, title, icon: Icon, accent, glow, bg }) => (
                <Grid item xs={12} sm={6} key={key}>
                    <Paper
                        elevation={0}
                        sx={{
                            background: 'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
                            border: `1px solid ${P.border}`,
                            borderRadius: '14px',
                            p: 2.25,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            boxShadow: '0 4px 20px rgba(0,0,0,0.35)',
                            transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                            '&:hover': {
                                borderColor: `${accent}44`,
                                boxShadow: `0 4px 24px rgba(0,0,0,0.4), 0 0 0 1px ${accent}22`,
                            },
                        }}
                    >
                        <Box>
                            <Typography sx={{
                                color: P.dim,
                                fontSize: '0.62rem',
                                fontWeight: 700,
                                letterSpacing: '0.1em',
                                textTransform: 'uppercase',
                                mb: 0.5,
                            }}>
                                {title}
                            </Typography>
                            <Typography sx={{
                                color: '#f1f5f9',
                                fontSize: '1.75rem',
                                fontWeight: 800,
                                lineHeight: 1,
                                letterSpacing: '-0.02em',
                            }}>
                                {(data[key as keyof typeof data] as number).toLocaleString()}
                            </Typography>
                        </Box>

                        <Box sx={{
                            width: 44,
                            height: 44,
                            borderRadius: '12px',
                            background: bg,
                            border: `1px solid ${accent}33`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            boxShadow: `0 0 16px ${glow}`,
                            flexShrink: 0,
                        }}>
                            <Icon size={20} color={accent} stroke={1.5} />
                        </Box>
                    </Paper>
                </Grid>
            ))}
        </Grid>
    );
};