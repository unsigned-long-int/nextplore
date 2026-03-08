import { Box, Divider, Paper, Typography } from '@mui/material';
import {
    AlternateEmail as AtIcon,
    Business as OrgIcon,
    AutoAwesome as SparkleIcon,
} from '@mui/icons-material';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';
import { UserStats } from '@/features/user/components/UserStats';
import { useUserProfile } from '@/features/user/hooks/useUserProfile';

const P = {
    border: 'rgba(168,85,247,0.18)',
    soft:   'rgba(168,85,247,0.08)',
    icon:   '#a855f7',
    label:  '#c084fc',
    dim:    'rgba(255,255,255,0.28)',
};

const nameToHue = (name: string) =>
    name.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) % 360;

export const UserProfilePage = () => {
    const { isPending, isError, error, data } = useUserProfile();

    if (isPending) return <LoadingOverlay loadingText="Getting user data…" />;
    if (isError) return (
        <Typography sx={{ color: '#f87171', fontSize: '0.82rem' }}>{error.message}</Typography>
    );
    if (!data) return (
        <Typography sx={{ color: P.dim, fontSize: '0.82rem' }}>No user data available.</Typography>
    );

    const initials = data.name
        .split(' ')
        .map((w: string) => w[0])
        .join('')
        .slice(0, 2)
        .toUpperCase();

    const hue = nameToHue(data.name);

    return (
        <Box sx={{ maxWidth: 680 }}>
            <Paper
                elevation={0}
                sx={{
                    background: 'linear-gradient(145deg, #0d0f1e 0%, #0f1228 100%)',
                    border: `1px solid ${P.border}`,
                    borderRadius: '16px',
                    p: 3,
                    boxShadow: '0 8px 32px rgba(0,0,0,0.45), 0 0 0 1px rgba(168,85,247,0.05)',
                    mb: 2.5,
                }}
            >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2.5 }}>
                    <Box sx={{ flexShrink: 0 }}>
                        <Box sx={{
                            width: 72,
                            height: 72,
                            borderRadius: '16px',
                            background: `linear-gradient(135deg,
                                hsl(${hue}, 70%, 35%) 0%,
                                hsl(${(hue + 40) % 360}, 80%, 55%) 100%)`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            boxShadow: `0 0 24px hsla(${hue}, 70%, 45%, 0.35)`,
                            border: `1px solid hsla(${hue}, 70%, 55%, 0.25)`,
                            fontSize: '1.3rem',
                            fontWeight: 800,
                            color: '#fff',
                            letterSpacing: '-0.02em',
                        }}>
                            {initials}
                        </Box>
                    </Box>

                    <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 0.5 }}>
                            <SparkleIcon sx={{ fontSize: 11, color: P.icon }} />
                            <Typography sx={{
                                color: P.icon,
                                fontSize: '0.62rem',
                                fontWeight: 700,
                                letterSpacing: '0.1em',
                                textTransform: 'uppercase',
                            }}>
                                {data.role}
                            </Typography>
                        </Box>

                        <Typography sx={{
                            color: '#f1f5f9',
                            fontSize: '1.2rem',
                            fontWeight: 700,
                            letterSpacing: '-0.01em',
                            mb: 1.25,
                            lineHeight: 1.2,
                        }}>
                            {data.name}
                        </Typography>

                        <Divider sx={{ borderColor: 'rgba(168,85,247,0.1)', mb: 1.25 }} />

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.75 }}>
                            <Box sx={{
                                width: 24, height: 24, borderRadius: '7px',
                                background: P.soft,
                                border: `1px solid ${P.border}`,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                flexShrink: 0,
                            }}>
                                <AtIcon sx={{ fontSize: 13, color: P.icon }} />
                            </Box>
                            <Typography sx={{ color: P.dim, fontSize: '0.82rem' }}>
                                {data.email}
                            </Typography>
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box sx={{
                                width: 24, height: 24, borderRadius: '7px',
                                background: P.soft,
                                border: `1px solid ${P.border}`,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                flexShrink: 0,
                            }}>
                                <OrgIcon sx={{ fontSize: 13, color: P.icon }} />
                            </Box>
                            <Typography sx={{ color: P.dim, fontSize: '0.82rem' }}>
                                {data.organization}
                            </Typography>
                        </Box>
                    </Box>
                </Box>
            </Paper>

            <UserStats />
        </Box>
    );
};