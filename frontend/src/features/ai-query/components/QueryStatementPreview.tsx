import { Box, Paper, Typography } from '@mui/material';
import { Code as CodeIcon } from '@mui/icons-material';
import { QueryStatementCopyButton } from '@/features/ai-query/components/QueryStatementCopyButton';
import { SqlHighlight } from "@/features/ai-query/components/SqlHighlight.tsx";

export const QueryStatementPreview = ({ sql }: { sql: string }) => {
    if (!sql) return null;

    return (
        <Paper
            elevation={0}
            sx={{
                background: 'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
                border: '1px solid rgba(168,85,247,0.15)',
                borderRadius: '16px',
                overflow: 'hidden',
                boxShadow: '0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(168,85,247,0.05)',
                mb: 2,
            }}
        >
            <Box
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    px: 2.5,
                    py: 1.5,
                    borderBottom: '1px solid rgba(168,85,247,0.1)',
                    background: 'rgba(168,85,247,0.04)',
                }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CodeIcon sx={{ fontSize: 13, color: '#a855f7' }} />
                    <Typography
                        sx={{
                            color: '#a855f7',
                            fontWeight: 700,
                            fontSize: '0.65rem',
                            letterSpacing: '0.1em',
                            textTransform: 'uppercase',
                        }}
                    >
                        Generated SQL
                    </Typography>
                </Box>
                <QueryStatementCopyButton sql={sql} />
            </Box>

            <Box
                component="pre"
                sx={{
                    m: 0,
                    px: 2.5,
                    py: 2,
                    fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
                    fontSize: '0.82rem',
                    lineHeight: 1.7,
                    color: '#e2e8f0',
                    overflowX: 'auto',
                    whiteSpace: 'pre',
                    background: 'transparent',
                    scrollbarColor: 'rgba(168,85,247,0.25) transparent',
                    scrollbarWidth: 'thin',
                    '&::-webkit-scrollbar': { height: 5 },
                    '&::-webkit-scrollbar-thumb': {
                        background: 'rgba(168,85,247,0.25)',
                        borderRadius: 3,
                    },
                    '&::-webkit-scrollbar-track': { background: 'transparent' },

                    '& .kw': { color: '#c084fc', fontWeight: 600 },
                }}
            >
                <SqlHighlight sql={sql} />
            </Box>
        </Paper>
    );
};
