import {
    Box,
    Paper,
    Button,
    Typography,
} from '@mui/material';
import {IconSparkles} from "@tabler/icons-react";


export const CacheHitBadge = ({ onRunFresh }: { onRunFresh: () => void }) => (
    <Paper
        elevation={0}
        sx={{
            background: 'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
            border: '1px solid rgba(168,85,247,0.18)',
            borderRadius: '16px',
            px: 2.5,
            py: 1.5,
            mb: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 2,
        }}
    >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
            <Box sx={{
                width: 24, height: 24, borderRadius: '7px',
                background: 'rgba(168,85,247,0.08)',
                border: '1px solid rgba(168,85,247,0.18)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
            }}>
                <IconSparkles size={13} color="#a855f7" />
            </Box>
            <Box>
                <Typography sx={{
                    color: '#c084fc', fontSize: '0.68rem', fontWeight: 700,
                    letterSpacing: '0.1em', textTransform: 'uppercase',
                }}>
                    Served from cache
                </Typography>
                <Typography sx={{ color: 'rgba(255,255,255,0.28)', fontSize: '0.75rem', mt: 0.25 }}>
                    Pipeline trace not available - this response was cached from a previous run
                </Typography>
            </Box>
        </Box>

        <Button
            size="small"
            onClick={onRunFresh}
            sx={{
                background: 'rgba(168,85,247,0.08)',
                color: 'rgba(196,132,252,0.85)',
                border: '1px solid rgba(168,85,247,0.2)',
                borderRadius: '9px',
                fontSize: '0.72rem',
                fontWeight: 600,
                textTransform: 'none',
                px: 1.75,
                height: 30,
                whiteSpace: 'nowrap',
                flexShrink: 0,
                transition: 'all 0.15s ease',
                '&:hover': {
                    background: 'rgba(168,85,247,0.18)',
                    borderColor: 'rgba(168,85,247,0.45)',
                    color: '#c084fc',
                    boxShadow: '0 0 14px rgba(168,85,247,0.25)',
                },
            }}
        >
            Run fresh
        </Button>
    </Paper>
);