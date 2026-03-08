import { useState, KeyboardEvent } from 'react';
import {
    Box,
    TextField,
    Button,
    Paper,
    Typography,
    InputAdornment,
    CircularProgress,
    Chip,
} from '@mui/material';
import { Search as SearchIcon, AutoAwesome as AutoAwesomeIcon } from '@mui/icons-material';

interface Props {
    prompt: string;
    setPrompt: (val: string) => void;
    onSubmit: () => void;
    loading: boolean;
}

const suggestions = [
    'Avg expense per person last year',
    'Top cost centers this quarter',
    'German entity breakdown',
];

export const PromptBox = ({ prompt, setPrompt, onSubmit, loading }: Props) => {
    const [focused, setFocused] = useState(false);

    const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            if (!loading && prompt.trim()) onSubmit();
        }
    };

    return (
        <Paper
            elevation={0}
            sx={{
                background: 'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
                border: '1px solid',
                borderColor: focused ? 'rgba(168, 85, 247, 0.5)' : 'rgba(255,255,255,0.07)',
                borderRadius: '16px',
                p: 2.5,
                transition: 'border-color 0.25s ease, box-shadow 0.25s ease',
                boxShadow: focused
                    ? '0 0 0 3px rgba(168, 85, 247, 0.1), 0 8px 32px rgba(0,0,0,0.5)'
                    : '0 4px 20px rgba(0,0,0,0.4)',
            }}
        >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <AutoAwesomeIcon sx={{ fontSize: 13, color: '#a855f7' }} />
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
                    Natural Language Query
                </Typography>
            </Box>

            <TextField
                multiline
                minRows={2}
                maxRows={6}
                fullWidth
                variant="outlined"
                placeholder="e.g., Show me average expense per person for the last year for German entity"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                onKeyDown={handleKeyDown}
                InputProps={{
                    startAdornment: (
                        <InputAdornment position="start" sx={{ alignSelf: 'flex-start', mt: 1.5 }}>
                            <SearchIcon sx={{ color: 'rgba(168,85,247,0.35)', fontSize: 18 }} />
                        </InputAdornment>
                    ),
                }}
                sx={{
                    '& .MuiOutlinedInput-root': {
                        background: 'rgba(168,85,247,0.04)',
                        borderRadius: '10px',
                        color: '#e2e8f0',
                        fontSize: '0.9rem',
                        lineHeight: 1.6,
                        '& fieldset': { border: '1px solid rgba(168,85,247,0.15)' },
                        '&:hover fieldset': { borderColor: 'rgba(168,85,247,0.3)' },
                        '&.Mui-focused fieldset': { borderColor: 'rgba(168,85,247,0.6)', borderWidth: '1px' },
                    },
                    '& .MuiInputBase-input::placeholder': {
                        color: 'rgba(255,255,255,0.18)',
                        fontStyle: 'italic',
                    },
                }}
            />

            <Box sx={{ display: 'flex', gap: 0.75, mt: 1.5, flexWrap: 'wrap' }}>
                {suggestions.map((s) => (
                    <Chip
                        key={s}
                        label={s}
                        size="small"
                        onClick={() => setPrompt(s)}
                        sx={{
                            background: 'rgba(168,85,247,0.08)',
                            color: 'rgba(196,132,252,0.8)',
                            border: '1px solid rgba(168,85,247,0.2)',
                            borderRadius: '6px',
                            fontSize: '0.7rem',
                            fontWeight: 500,
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                            '&:hover': {
                                background: 'rgba(168,85,247,0.18)',
                                borderColor: 'rgba(168,85,247,0.45)',
                                color: '#c084fc',
                                boxShadow: '0 0 10px rgba(168,85,247,0.2)',
                            },
                        }}
                    />
                ))}
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 2 }}>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.15)', fontSize: '0.7rem' }}>
                    ⌘ + Enter to run
                </Typography>

                <Button
                    variant="contained"
                    onClick={onSubmit}
                    disabled={loading || !prompt.trim()}
                    startIcon={
                        loading
                            ? <CircularProgress size={14} sx={{ color: 'rgba(255,255,255,0.5)' }} />
                            : <SearchIcon sx={{ fontSize: '16px !important' }} />
                    }
                    sx={{
                        background: loading
                            ? 'rgba(168,85,247,0.15)'
                            : 'linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #c084fc 100%)',
                        color: loading ? 'rgba(255,255,255,0.3)' : '#fff',
                        fontWeight: 700,
                        fontSize: '0.8rem',
                        letterSpacing: '0.04em',
                        textTransform: 'none',
                        px: 2.5,
                        py: 0.9,
                        borderRadius: '10px',
                        boxShadow: loading ? 'none' : '0 0 20px rgba(168,85,247,0.35)',
                        border: 'none',
                        transition: 'all 0.2s ease',
                        '&:hover': {
                            background: 'linear-gradient(135deg, #6d28d9 0%, #9333ea 50%, #a855f7 100%)',
                            boxShadow: '0 0 28px rgba(168,85,247,0.5)',
                            transform: 'translateY(-1px)',
                        },
                        '&:active': { transform: 'translateY(0)' },
                        '&.Mui-disabled': {
                            background: 'rgba(255,255,255,0.05)',
                            color: 'rgba(255,255,255,0.2)',
                        },
                    }}
                >
                    {loading ? 'Running…' : 'Run Query'}
                </Button>
            </Box>
        </Paper>
    );
};