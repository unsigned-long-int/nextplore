import {
    Autocomplete,
    Box,
    Divider,
    Fade,
    Paper,
    Typography,
} from '@mui/material';
import { styled } from '@mui/system';
import {
    AutoAwesome as AutoAwesomeIcon,
    ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import {
    IconAtom,
    IconBrain, IconPackage,
    IconCloud, IconPlugConnected,
    IconRobot,
    IconSparkles,
} from '@tabler/icons-react';
import { type ReactNode, useEffect, useMemo, useState } from 'react';
import { PipelineTrace } from '@/features/ai-query/components/LlmPipelineTrace';
import { PromptBox } from '@/features/ai-query/components/PromptBox';
import { QueryStatementPreview } from '@/features/ai-query/components/QueryStatementPreview';
import { QueryResultTable } from '@/features/ai-query/components/QueryResultTable';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';
import { useGetModels } from '@/features/ai-query/hooks/useGetModels';
import { useGetAiResponse } from '@/features/ai-query/hooks/useGetAiResponse';
import type {LlmProfile, PipelineTrace as PipelineTraceData} from '@/shared/api/services/ai-query/types.gen';
import {LlmSource} from "@/shared/api/services/ai-query/types.gen";

const P = {
    glow: 'rgba(168,85,247,0.45)',
    border: 'rgba(168,85,247,0.18)',
    soft: 'rgba(168,85,247,0.08)',
    label: '#c084fc',
    icon: '#a855f7',
    dim: 'rgba(255,255,255,0.18)',
};

const BADGE_CONFIG = {
    [LlmSource.PLATFORM]: {
        icon: <IconPackage size={10} />,
        label: 'Built-in',
        color: '#38bdf8',
        background: 'rgba(56,189,248,0.1)',
        border: 'rgba(56,189,248,0.25)',
    },
    [LlmSource.USER]: {
        icon: <IconPlugConnected size={10} />,
        label: 'Custom',
        color: '#c084fc',
        background: 'rgba(168,85,247,0.1)',
        border: 'rgba(168,85,247,0.25)',
    },
} as const;

interface ModelSourceBadgeProps {
    source: LlmSource;
}

export const ModelSourceBadge = ({ source }: ModelSourceBadgeProps) => {
    const config = BADGE_CONFIG[source];
    if (!config) return null;

    return (
        <Box
            sx={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                px: '5px',
                py: '2px',
                borderRadius: '4px',
                background: config.background,
                border: `1px solid ${config.border}`,
                color: config.color,
                fontSize: '0.62rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                lineHeight: 1,
                flexShrink: 0,
            }}
        >
            {config.icon}
            {config.label}
        </Box>
    );
};

const modelIcons: Record<string, ReactNode> = {
    'moonshotai': <IconRobot size={14} />,
    'meta-llama': <IconBrain size={14} />,
    'qwen': <IconCloud size={14} />,
    'deepseek': <IconAtom size={14} />,
    'gpt-4o': <IconSparkles size={14} />,
    'default': <IconRobot  size={14} />,
};

interface ModelOption {
    model_id: string;
    label: string;
    provider: string;
    icon?: ReactNode;
    source: LlmSource;
    model_ref_id?: string | null;
}

const Toast = ({ message, type }: { message: string; type: 'error' }) => (
    <Box sx={{
        position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
        background: 'linear-gradient(135deg, #1c0b0b 0%, #450a0a 100%)',
        border: '1px solid rgba(239,68,68,0.3)',
        borderRadius: '12px', px: 2.5, py: 1.5,
        display: 'flex', alignItems: 'center', gap: 1.5,
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)', maxWidth: 360,
        animation: 'slideUp 0.25s ease',
        '@keyframes slideUp': {
            from: { opacity: 0, transform: 'translateY(12px)' },
            to:   { opacity: 1, transform: 'translateY(0)' },
        },
    }}>
        <Typography sx={{ color: '#fca5a5', fontSize: '0.82rem', fontWeight: 500, lineHeight: 1.4 }}>
            {message}
        </Typography>
    </Box>
);

const GroupHeader = styled('div')({
    position: 'sticky',
    top: '-8px',
    padding: '4px 10px',
    color: P.label,
    backgroundColor: 'rgba(168,85,247,0.08)',
    fontSize: '0.7rem',
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    borderBottom: `1px solid ${P.border}`,
});


const GroupItems = styled('ul')({
    padding: 0,
});

export const AiQueryPage = () => {
    const [prompt, setPrompt] = useState('');
    const [selectedModel, setSelectedModel] = useState<string | null>(null);
    const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
    const [selectedModelRef, setSelectedModelRef] = useState<string | null>(null);
    const [selectedModelSource, setSelectedModelSource] = useState<LlmSource | null>(null);
    const [inputValue, setInputValue] = useState('');
    const [aiQueryResponse, setAiQueryResponse] = useState<{ [key: string]: string }[]>([]);
    const [sqlPreview, setSqlPreview] = useState('');
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [pipelineTrace, setPipelineTrace] = useState<PipelineTraceData | undefined>(undefined);

    const { data = [], isError, isSuccess, error } = useGetModels();
    const getAiResponse = useGetAiResponse();

    const modelOptions: ModelOption[] = useMemo(() =>
        (data as LlmProfile[]).map((m) => ({
            provider: m.provider,
            model_id: m.model_id,
            label: `${m.label} (${m.tags.join(', ')})`,
            icon: modelIcons[m.model_id?.toLowerCase() ?? ''] ?? modelIcons.default,
            source: m.source,
            model_ref_id: m.model_ref_id
        })), [data]);

    const handleAiQueryRequest = async () => {
        if (!selectedModel || !selectedProvider || !selectedModelSource) return;
        setErrorMessage(null);
        setSqlPreview('');
        setAiQueryResponse([]);
        setPipelineTrace(undefined);

        try {
            const response = await getAiResponse.mutateAsync({
                provider: selectedProvider,
                model_id: selectedModel,
                model_ref_id: selectedModelRef,
                is_user_model: selectedModelSource === LlmSource.USER,
                prompt: prompt,
            });
            setAiQueryResponse(response.data);
            setSqlPreview(response.sql);
            setPipelineTrace(response.trace);
        } catch (e: any) {
            setErrorMessage(e.message);
        }
    };

    useEffect(() => {
        if (isSuccess && modelOptions.length > 0 && !selectedModel) {
            setSelectedModel(modelOptions[0].model_id);
            setSelectedProvider(modelOptions[0].provider);
            setSelectedModelRef(modelOptions[0].model_ref_id ?? null);
            setSelectedModelSource(modelOptions[0].source);
            setInputValue(modelOptions[0].label);
        }
    }, [isSuccess, modelOptions, selectedModel]);

    useEffect(() => {
        if (isError) {
            const msg = (error as { message?: string } | undefined)?.message ?? 'Models retrieval failed';
            setErrorMessage(msg);
            setTimeout(() => setErrorMessage(null), 8000);
        }
    }, [isError, error]);

    const loading = getAiResponse.isPending;
    const showResults = !loading && !!sqlPreview;

    return (
        <Box sx={{ maxWidth: 900, mx: 'auto' }}>

            <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 0.75 }}>
                    <AutoAwesomeIcon sx={{ fontSize: 18, color: P.icon }} />
                    <Typography sx={{
                        color: '#f1f5f9',
                        fontWeight: 700,
                        fontSize: '1.35rem',
                        letterSpacing: '-0.01em',
                    }}>
                        Request any data from database
                    </Typography>
                </Box>
                <Typography sx={{ color: P.dim, fontSize: '0.82rem', pl: '26px' }}>
                    Example: "Total number of characters in Marvel movies?"
                </Typography>
            </Box>

            <Paper
                elevation={0}
                sx={{
                    background: 'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
                    border: `1px solid ${P.border}`,
                    borderRadius: '16px',
                    p: 2.5,
                    mb: 2,
                    boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
                }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                    <IconRobot size={13} color={P.icon} />
                    <Typography sx={{
                        color: P.icon, fontWeight: 700,
                        fontSize: '0.65rem', letterSpacing: '0.1em', textTransform: 'uppercase',
                    }}>
                        LLM Model
                    </Typography>
                </Box>

                <Autocomplete
                    options={modelOptions}
                    groupBy={(option) => option.source === LlmSource.PLATFORM ? 'Platform Models' : 'Custom Models'}
                    getOptionLabel={(opt) => typeof opt === 'string' ? opt : opt.label}
                    inputValue={inputValue}
                    onInputChange={(_, val) => setInputValue(val)}
                    onChange={(_, opt) => {
                        if (opt && typeof opt !== 'string') {
                            setSelectedModel(opt.model_id);
                            setSelectedProvider(opt.provider);
                            setSelectedModelRef(opt.model_ref_id ?? null);
                            setSelectedModelSource(opt.source);
                            setInputValue(opt.label);
                        }
                    }}
                    popupIcon={<ExpandMoreIcon sx={{ color: P.icon, fontSize: 18 }} />}
                    noOptionsText={
                        <Typography sx={{ color: P.dim, fontSize: '0.82rem' }}>
                            Nothing found
                        </Typography>
                    }
                    renderOption={({key, ...options}, opt) => (
                        <Box
                            component="li"
                            key={key}
                            {...options}
                            sx={{
                                display: 'flex', alignItems: 'center', gap: 1.25,
                                px: '12px !important', py: '9px !important',
                                borderRadius: '8px',
                                justifyContent: 'space-between',
                                mx: '4px',
                                color: '#94a3b8',
                                fontSize: '0.84rem',
                                cursor: 'pointer',
                                transition: 'all 0.15s ease',
                                '&:hover, &.Mui-focused': {
                                    background: `${P.soft} !important`,
                                    color: '#f1f5f9',
                                },
                                '&[aria-selected="true"]': {
                                    background: 'rgba(168,85,247,0.12) !important',
                                    color: P.label,
                                },
                            }}
                        >
                       <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, minWidth: 0 }}>
                                <Box sx={{ color: P.icon, display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                                    {opt.icon}
                                </Box>
                                <Box sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {opt.label}
                                </Box>
                            </Box>
                        </Box>
                    )}
                    slotProps={{
                        paper: {
                            sx: {
                                background: 'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
                                border: `1px solid ${P.border}`,
                                borderRadius: '12px',
                                boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
                                mt: 0.5,
                                '& .MuiAutocomplete-listbox': { py: 0.75 },
                            },
                        },
                    }}
                    renderInput={(params) => (
                        <Box ref={params.InputProps.ref}>
                            <input
                                {...params.inputProps}
                                placeholder="Search model..."
                                style={{
                                    width: '100%',
                                    background: 'rgba(168,85,247,0.05)',
                                    border: '1px solid rgba(168,85,247,0.2)',
                                    borderRadius: '10px',
                                    color: '#e2e8f0',
                                    fontSize: '0.88rem',
                                    padding: '10px 40px 10px 14px',
                                    outline: 'none',
                                    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                                    fontFamily: 'inherit',
                                }}
                                onFocus={(e) => {
                                    e.target.style.borderColor = 'rgba(168,85,247,0.55)';
                                    e.target.style.boxShadow = '0 0 0 3px rgba(168,85,247,0.1)';
                                }}
                                onBlur={(e) => {
                                    e.target.style.borderColor = 'rgba(168,85,247,0.2)';
                                    e.target.style.boxShadow = 'none';
                                }}
                            />
                            <Box sx={{
                                position: 'absolute', right: 10, top: '50%',
                                transform: 'translateY(-50%)', pointerEvents: 'none',
                                display: 'flex', alignItems: 'center',
                                color: P.icon,
                            }}>
                                {params.InputProps.endAdornment}
                            </Box>
                        </Box>
                    )}
                    sx={{ position: 'relative', maxWidth: 420 }}
                    renderGroup={(params) => (
                        <li key={params.key}>
                          <GroupHeader>{params.group}</GroupHeader>
                          <GroupItems>{params.children}</GroupItems>
                        </li>
                    )}
                />
                {selectedModelSource && (
                    <Fade in={!!selectedModelSource} timeout={200}>
                        <Box>
                            <ModelSourceBadge source={selectedModelSource} />
                        </Box>
                    </Fade>
                )}
            </Paper>

            <PromptBox
                prompt={prompt}
                setPrompt={setPrompt}
                onSubmit={handleAiQueryRequest}
                loading={loading}
            />

            {errorMessage && !isError && (
                <Box sx={{ mt: 1.5, mb: 0.5, textAlign: 'center' }}>
                    <Typography sx={{
                        color: '#f87171', fontSize: '0.82rem',
                        background: 'rgba(239,68,68,0.07)',
                        border: '1px solid rgba(239,68,68,0.2)',
                        borderRadius: '8px', px: 2, py: 1, display: 'inline-block',
                    }}>
                        {errorMessage}
                    </Typography>
                </Box>
            )}

            <Divider sx={{ borderColor: P.border, my: 3 }} />

            <Box sx={{ position: 'relative', minHeight: 260, overflow: 'hidden' }}>
                {loading && (
                    <LoadingOverlay loadingText="Asking the model... LLM snail is inspecting it..." />
                )}

                <Fade in={showResults} timeout={400}>
                    <Box>
                        <PipelineTrace
                            trace={pipelineTrace}
                            visible={showResults}
                        />

                        <QueryStatementPreview sql={sqlPreview} />
                        <QueryResultTable data={aiQueryResponse} />
                    </Box>
                </Fade>
            </Box>

            {errorMessage && isError && <Toast message={errorMessage} type="error" />}
        </Box>
    );
};