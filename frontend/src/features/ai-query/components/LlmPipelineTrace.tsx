import { Box, Chip, Collapse, LinearProgress, Paper, Typography } from '@mui/material';
import {
    AccountTree as TreeIcon,
    ExpandMore as ExpandMoreIcon,
    Search as SearchIcon,
    Sort as SortIcon,
    TableChart as TableIcon,
    KeyboardArrowRight as ArrowIcon,
} from '@mui/icons-material';
import { useEffect, useState } from 'react';
import type {
    PipelineTrace as PipelineTraceData,
    RrfEntry,
    SubQuerySearchResult
} from '@/shared/api/services/ai-query/types.gen';


export const DUMMY_TRACE: PipelineTraceData = {
    original_query: 'what is average salary per month?',
    sub_queries: [
        'average expense per employee last year',
        'per-person cost breakdown 2024 german entity',
        'employee spending report annual',
    ],
    vector_hits: [
        {
            sub_query: 'average expense per employee last year',
            vector_hits: [
                { table: 'expenses',      score: 0.93, snippet: 'amount, date, employee_id' },
                { table: 'employees',     score: 0.88, snippet: 'id, name, entity' },
                { table: 'cost_centers',  score: 0.71, snippet: 'id, name, budget' },
                { table: 'entities',      score: 0.64, snippet: 'id, country, name' },
            ],
        },
        {
            sub_query: 'per-person cost breakdown 2024 german entity',
            vector_hits: [
                { table: 'expenses',      score: 0.89, snippet: 'amount, currency, date' },
                { table: 'entities',      score: 0.85, snippet: 'id, country, name' },
                { table: 'employees',     score: 0.76, snippet: 'id, entity_id' },
                { table: 'cost_centers',  score: 0.58, snippet: 'id, entity_id' },
            ],
        },
        {
            sub_query: 'employee spending report annual',
            vector_hits: [
                { table: 'employees',     score: 0.91, snippet: 'id, name, department' },
                { table: 'expenses',      score: 0.84, snippet: 'employee_id, amount' },
                { table: 'departments',   score: 0.62, snippet: 'id, name' },
                { table: 'cost_centers',  score: 0.55, snippet: 'department_id' },
            ],
        },
    ],
    rrf_ranking: [
        { table: 'expenses',     rrf_score: 0.051, rank: 1 },
        { table: 'employees',    rrf_score: 0.047, rank: 2 },
        { table: 'entities',     rrf_score: 0.033, rank: 3 },
        { table: 'cost_centers', rrf_score: 0.029, rank: 4 },
        { table: 'departments',  rrf_score: 0.018, rank: 5 },
    ],
    schema_context: ['expenses', 'employees', 'entities'],
};

const P = {
    border: 'rgba(168,85,247,0.18)',
    soft:   'rgba(168,85,247,0.08)',
    icon:   '#a855f7',
    label:  '#c084fc',
    dim:    'rgba(255,255,255,0.28)',
    text:   '#cbd5e1',
};


const StageHeader = ({
    icon,
    label,
    count,
}: {
    icon: React.ReactNode;
    label: string;
    count?: string;
}) => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.25 }}>
        <Box sx={{
            width: 24, height: 24, borderRadius: '7px',
            background: P.soft, border: `1px solid ${P.border}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
        }}>
            {icon}
        </Box>
        <Typography sx={{
            color: P.label, fontSize: '0.68rem', fontWeight: 700,
            letterSpacing: '0.1em', textTransform: 'uppercase',
        }}>
            {label}
        </Typography>
        {count && (
            <Chip label={count} size="small" sx={{
                background: P.soft, color: 'rgba(196,132,252,0.7)',
                border: `1px solid ${P.border}`, borderRadius: '6px',
                fontSize: '0.62rem', fontWeight: 600, height: 18,
                '& .MuiChip-label': { px: 0.75 },
            }} />
        )}
        <Box sx={{
            flex: 1, height: '1px',
            background: `linear-gradient(90deg, ${P.border}, transparent)`,
        }} />
    </Box>
);

const ScoreBar = ({ score, maxScore = 1 }: { score: number; maxScore?: number }) => {
    const pct = (score / maxScore) * 100;
    const color = pct > 75 ? '#a855f7' : pct > 50 ? '#38bdf8' : '#64748b';
    return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <LinearProgress
                variant="determinate"
                value={pct}
                sx={{
                    width: 80, height: 3, borderRadius: 2,
                    bgcolor: 'rgba(255,255,255,0.06)',
                    '& .MuiLinearProgress-bar': {
                        borderRadius: 2,
                        background: `linear-gradient(90deg, ${color}88, ${color})`,
                    },
                }}
            />
            <Typography sx={{ color, fontSize: '0.68rem', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                {score.toFixed(2)}
            </Typography>
        </Box>
    );
};

const QueryExpansionStage = ({ queries }: { queries: string[] }) => (
    <Box>
        <StageHeader
            icon={<TreeIcon sx={{ fontSize: 13, color: P.icon }} />}
            label="Query Expansion"
            count={`${queries.length} sub-queries`}
        />
        <Box sx={{ pl: '32px', display: 'flex', flexDirection: 'column', gap: 0.6 }}>
            {queries.map((q, i) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    <ArrowIcon sx={{ fontSize: 13, color: P.icon, mt: '2px', flexShrink: 0 }} />
                    <Typography sx={{
                        color: P.text, fontSize: '0.8rem', lineHeight: 1.5,
                        fontStyle: 'italic',
                    }}>
                        "{q}"
                    </Typography>
                </Box>
            ))}
        </Box>
    </Box>
);

const VectorSearchStage = ({ results }: { results: SubQuerySearchResult[] }) => {
    const [expanded, setExpanded] = useState<number | null>(0);

    return (
        <Box>
            <StageHeader
                icon={<SearchIcon sx={{ fontSize: 13, color: P.icon }} />}
                label="Vector Search"
                count={`${results.length} queries × top-${results[0]?.vector_hits.length ?? 0}`}
            />
            <Box sx={{ pl: '32px', display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                {results.map((result, i) => (
                    <Box key={i} sx={{
                        border: `1px solid ${expanded === i ? P.border : 'rgba(255,255,255,0.05)'}`,
                        borderRadius: '9px',
                        overflow: 'hidden',
                        transition: 'border-color 0.15s ease',
                    }}>
                        <Box
                            onClick={() => setExpanded(expanded === i ? null : i)}
                            sx={{
                                display: 'flex', alignItems: 'center', gap: 1,
                                px: 1.5, py: 0.9, cursor: 'pointer',
                                background: expanded === i ? P.soft : 'rgba(255,255,255,0.02)',
                                transition: 'background 0.15s ease',
                                '&:hover': { background: P.soft },
                            }}
                        >
                            <ExpandMoreIcon sx={{
                                fontSize: 14, color: P.icon,
                                transform: expanded === i ? 'rotate(0deg)' : 'rotate(-90deg)',
                                transition: 'transform 0.2s ease',
                            }} />
                            <Typography sx={{
                                color: P.dim, fontSize: '0.75rem', flex: 1,
                                fontStyle: 'italic', overflow: 'hidden',
                                textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                            }}>
                                "{result.sub_query}"
                            </Typography>
                            <Typography sx={{ color: 'rgba(168,85,247,0.5)', fontSize: '0.65rem' }}>
                                {result.vector_hits.length} hits
                            </Typography>
                        </Box>

                        {/* Hits table */}
                        <Collapse in={expanded === i}>
                            <Box sx={{ px: 1.5, pt: 0.5, pb: 1 }}>
                                {result.vector_hits.map((hit, j) => (
                                    <Box key={j} sx={{
                                        display: 'grid',
                                        gridTemplateColumns: '130px 1fr auto',
                                        alignItems: 'center',
                                        gap: 1.5,
                                        py: 0.6,
                                        borderBottom: j < result.vector_hits.length - 1
                                            ? '1px solid rgba(255,255,255,0.04)'
                                            : 'none',
                                    }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                                            <TableIcon sx={{ fontSize: 11, color: 'rgba(168,85,247,0.4)', flexShrink: 0 }} />
                                            <Typography sx={{
                                                color: '#e2e8f0', fontSize: '0.78rem',
                                                fontWeight: 600, fontFamily: 'monospace',
                                            }}>
                                                {hit.table}
                                            </Typography>
                                        </Box>
                                        <Typography sx={{
                                            color: 'rgba(255,255,255,0.2)', fontSize: '0.68rem',
                                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                        }}>
                                            {hit.snippet}
                                        </Typography>
                                        <ScoreBar score={hit.score} />
                                    </Box>
                                ))}
                            </Box>
                        </Collapse>
                    </Box>
                ))}
            </Box>
        </Box>
    );
};

const RrfRankingStage = ({ ranking }: { ranking: RrfEntry[] }) => {
    const maxScore = ranking[0]?.rrf_score ?? 1;
    return (
        <Box>
            <StageHeader
                icon={<SortIcon sx={{ fontSize: 13, color: P.icon }} />}
                label="Reciprocal Rank Fusion"
                count={`${ranking.length} tables`}
            />
            <Box sx={{ pl: '32px', display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                {ranking.map((entry, i) => (
                    <Box key={entry.table} sx={{
                        display: 'grid',
                        gridTemplateColumns: '24px 140px 1fr auto',
                        alignItems: 'center',
                        gap: 1.25,
                        py: 0.5,
                    }}>
                        <Typography sx={{
                            color: i < 3 ? P.icon : 'rgba(255,255,255,0.2)',
                            fontSize: '0.68rem', fontWeight: 700,
                            textAlign: 'right',
                        }}>
                            #{i + 1}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                            <TableIcon sx={{ fontSize: 11, color: i < 3 ? 'rgba(168,85,247,0.5)' : 'rgba(255,255,255,0.15)', flexShrink: 0 }} />
                            <Typography sx={{
                                color: i < 3 ? '#e2e8f0' : P.dim,
                                fontSize: '0.78rem', fontWeight: i < 3 ? 600 : 400,
                                fontFamily: 'monospace',
                            }}>
                                {entry.table}
                            </Typography>
                        </Box>
                        <LinearProgress
                            variant="determinate"
                            value={(entry.rrf_score / maxScore) * 100}
                            sx={{
                                height: 3, borderRadius: 2,
                                bgcolor: 'rgba(255,255,255,0.05)',
                                '& .MuiLinearProgress-bar': {
                                    borderRadius: 2,
                                    background: i < 3
                                        ? `linear-gradient(90deg, #7c3aed, #a855f7)`
                                        : 'rgba(255,255,255,0.15)',
                                },
                            }}
                        />
                        <Typography sx={{
                            color: i < 3 ? P.label : 'rgba(255,255,255,0.2)',
                            fontSize: '0.68rem', fontWeight: 700,
                            fontVariantNumeric: 'tabular-nums',
                            minWidth: 40, textAlign: 'right',
                        }}>
                            {entry.rrf_score.toFixed(3)}
                        </Typography>
                    </Box>
                ))}
            </Box>
        </Box>
    );
};

const SchemaContextStage = ({ tables }: { tables: string[] }) => (
    <Box>
        <StageHeader
            icon={<TableIcon sx={{ fontSize: 13, color: P.icon }} />}
            label="Schema Context Injected"
            count={`${tables.length} tables`}
        />
        <Box sx={{ pl: '32px', display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
            {tables.map((t) => (
                <Chip key={t} label={t} size="small" sx={{
                    background: 'rgba(168,85,247,0.1)',
                    color: P.label,
                    border: `1px solid rgba(168,85,247,0.25)`,
                    borderRadius: '6px',
                    fontSize: '0.72rem', fontWeight: 600,
                    fontFamily: 'monospace',
                    height: 22,
                    boxShadow: '0 0 8px rgba(168,85,247,0.15)',
                    '& .MuiChip-label': { px: 1 },
                }} />
            ))}
        </Box>
    </Box>
);

interface PipelineTraceProps {
    trace?: PipelineTraceData;
    visible: boolean;
}

export const PipelineTrace = ({ trace, visible }: PipelineTraceProps) => {
    const [open, setOpen] = useState(true);

    const [stageVisible, setStageVisible] = useState([false, false, false, false]);

    useEffect(() => {
        if (!visible) {
            setStageVisible([false, false, false, false]);
            return;
        }
        const delays = [0, 120, 280, 440];
        const timers = delays.map((d, i) =>
            setTimeout(() => setStageVisible((prev) => {
                const next = [...prev];
                next[i] = true;
                return next;
            }), d)
        );
        return () => timers.forEach(clearTimeout);
    }, [visible]);

    const data = trace ?? DUMMY_TRACE;

    if (!visible) return null;

    return (
        <Paper
            elevation={0}
            sx={{
                background: 'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
                border: `1px solid ${P.border}`,
                borderRadius: '16px',
                overflow: 'hidden',
                boxShadow: '0 8px 32px rgba(0,0,0,0.45)',
                mb: 2,
            }}
        >
            <Box
                onClick={() => setOpen((o) => !o)}
                sx={{
                    display: 'flex', alignItems: 'center', gap: 1,
                    px: 2.5, py: 1.6,
                    borderBottom: open ? `1px solid ${P.border}` : 'none',
                    background: 'rgba(168,85,247,0.04)',
                    cursor: 'pointer',
                    userSelect: 'none',
                    transition: 'background 0.15s ease',
                    '&:hover': { background: 'rgba(168,85,247,0.08)' },
                }}
            >
                <TreeIcon sx={{ fontSize: 13, color: P.icon }} />
                <Typography sx={{
                    color: P.icon, fontSize: '0.65rem', fontWeight: 700,
                    letterSpacing: '0.1em', textTransform: 'uppercase', flex: 1,
                }}>
                    Pipeline Trace
                </Typography>

                <Box sx={{ display: 'flex', gap: 0.5 }}>
                    {[
                        `${data.sub_queries.length} queries`,
                        `${data.vector_hits.reduce((a, r) => a + r.vector_hits.length, 0)} hits`,
                        `${data.rrf_ranking.length} ranked`,
                    ].map((label) => (
                        <Chip key={label} label={label} size="small" sx={{
                            background: 'rgba(168,85,247,0.07)',
                            color: 'rgba(196,132,252,0.6)',
                            border: `1px solid rgba(168,85,247,0.12)`,
                            borderRadius: '5px',
                            fontSize: '0.6rem', fontWeight: 600, height: 17,
                            '& .MuiChip-label': { px: 0.75 },
                        }} />
                    ))}
                </Box>

                <ExpandMoreIcon sx={{
                    fontSize: 16, color: P.icon, ml: 0.5,
                    transform: open ? 'rotate(0deg)' : 'rotate(-90deg)',
                    transition: 'transform 0.2s ease',
                }} />
            </Box>

            <Collapse in={open}>
                <Box sx={{ px: 2.5, py: 2, display: 'flex', flexDirection: 'column', gap: 2.5 }}>

                    <Box sx={{
                        opacity: stageVisible[0] ? 1 : 0,
                        transform: stageVisible[0] ? 'none' : 'translateY(6px)',
                        transition: 'opacity 0.3s ease, transform 0.3s ease',
                    }}>
                        <QueryExpansionStage queries={data.sub_queries} />
                    </Box>

                    <Box sx={{
                        opacity: stageVisible[1] ? 1 : 0,
                        transform: stageVisible[1] ? 'none' : 'translateY(6px)',
                        transition: 'opacity 0.3s ease, transform 0.3s ease',
                    }}>
                        <VectorSearchStage results={data.vector_hits} />
                    </Box>

                    <Box sx={{
                        opacity: stageVisible[2] ? 1 : 0,
                        transform: stageVisible[2] ? 'none' : 'translateY(6px)',
                        transition: 'opacity 0.3s ease, transform 0.3s ease',
                    }}>
                        <RrfRankingStage ranking={data.rrf_ranking} />
                    </Box>

                    <Box sx={{
                        opacity: stageVisible[3] ? 1 : 0,
                        transform: stageVisible[3] ? 'none' : 'translateY(6px)',
                        transition: 'opacity 0.3s ease, transform 0.3s ease',
                    }}>
                        <SchemaContextStage tables={data.schema_context} />
                    </Box>

                </Box>
            </Collapse>
        </Paper>
    );
};