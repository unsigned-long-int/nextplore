import { UnstyledButton, Box, Text, useMantineTheme, useMantineColorScheme, rgba } from '@mantine/core';
import { useMemo, useRef, useEffect } from 'react';
import awsLogo from '@/assets/aws-cloud.svg';
import azureLogo from '@/assets/azure-cloud.svg';
import gcpLogo from '@/assets/gcp-cloud.svg';

export type CloudProvider = 'aws' | 'azure' | 'gcp';

export const CLOUD_PROVIDERS: {id: CloudProvider; name: string; logoSrc: string}[] = [
    { id: 'aws', name: 'Amazon Web Services', logoSrc: awsLogo },
    { id: 'azure', name: 'Microsoft Azure', logoSrc: azureLogo },
    { id: 'gcp', name: 'Google Cloud Platform', logoSrc: gcpLogo },
];

type Props = {
    value: CloudProvider | null;
    onChange: (v: CloudProvider) => void;
    disabled?: boolean
};

export const DatastoreCloudProviderPicker = ({value, onChange, disabled}: Props) => {
    const theme = useMantineTheme();
    const { colorScheme } = useMantineColorScheme();
    const itemsRef = useRef<Array<HTMLButtonElement | null>>([]);

    const currentIndex = useMemo(
        () => CLOUD_PROVIDERS.findIndex((c) => c.id === value),
        [value]
    );

    useEffect(() => {
        if (currentIndex >= 0) itemsRef.current[currentIndex]?.focus();
    }, [currentIndex]);

    const ring = theme.colors.blue[6];
    const ringDark = theme.colors.blue[5];
    const border = colorScheme === 'dark' ? theme.colors.dark[4] : theme.colors.gray[3];
    const hoverBase = colorScheme === 'dark' ? theme.colors.dark[5] : theme.colors.gray[0];
    const selectedBg = colorScheme === 'dark' ? rgba(ringDark, 0.15) : rgba(ring, 0.08);
    const selectedBorder = colorScheme === 'dark' ? theme.colors.blue[5] : theme.colors.blue[6];

    const handleKey = (e: React.KeyboardEvent) => {
        if (disabled) return;
        const max = CLOUD_PROVIDERS.length - 1;
        let next = currentIndex;

        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            next = Math.min(max, currentIndex < 0 ? 0 : currentIndex + 1);
            e.preventDefault();
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            next = Math.max(0, currentIndex < 0 ? 0 : currentIndex -1);
            e.preventDefault();
        } else if (e.key === ' ' || e.key === 'Enter') {
            if (currentIndex >= 0) onChange(CLOUD_PROVIDERS[currentIndex].id);
            e.preventDefault();
        }
        if (next !== currentIndex && next >= 0) onChange(CLOUD_PROVIDERS[next].id);
    };

    return (
        <Box
            role='radiogroup'
            aria-label='Cloud Provider'
            onKeyDown={handleKey}
            style={{ display: 'flex', gap: 12,  flexWrap: 'wrap'}}
        >
            {CLOUD_PROVIDERS.map((cp, idx) => {
                const isSelected = value === cp.id;
                return (
                    <UnstyledButton
                        key={cp.id}
                        ref={(el) => { itemsRef.current[idx] = el;}}
                        type='button'
                        role='radio'
                        aria-checked={isSelected}
                        aria-label={cp.name}
                        disabled={disabled}
                        onClick={() => onChange(cp.id)}
                        style={{
                            width: 140,
                            height: 160,
                            padding: 12,
                            borderRadius: 16,
                            border: `1.5px solid ${isSelected ? selectedBorder : border}`,
                            background: isSelected ? selectedBg : 'transparent',
                            boxShadow: isSelected ?
                                `0 0 0 2px ${rgba(colorScheme === 'dark' ? ringDark : ring, 0.6)}`
                                : 'none',
                            outline: 'none',
                            transition: 'border-color 120ms ease, box-shadow 120ms ease, background 120ms ease, opacity 120ms ease, filter 120ms ease',
                            opacity: isSelected ? 1 : 0.8,
                            filter: !isSelected && colorScheme === 'light' ? 'grayscale(0.5)' : 'none',
                            cursor: disabled ? 'not-allowed' : 'pointer',
                        }}
                        onFocus={(e) => {
                            if (!isSelected) e.currentTarget.style.boxShadow = `0 0 0 2px ${rgba(theme.colors.gray[5], 0.5)}`;
                        }}
                        onBlur={(e) => {
                            if(!isSelected) e.currentTarget.style.boxShadow = 'none';
                        }}
                        onMouseEnter={(e) => {
                            if (!isSelected) e.currentTarget.style.background = rgba(hoverBase, colorScheme === 'dark' ? 0.3 : 0.6);
                        }}
                        onMouseLeave={(e) => {
                            if(!isSelected) e.currentTarget.style.background = 'transparent';
                        }}
                        >
                        <Box
                            style={{
                                width: 80,
                                height: 80,
                                margin: '0 auto',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                        >
                            <img
                                src={cp.logoSrc}
                                alt={cp.name}
                                style={{ width: 80, height: 80, objectFit: 'contain' }}
                            />
                        </Box>
                        <Text ta='center' size='sm' mt={8}>
                            {cp.name}
                        </Text>
                    </UnstyledButton>
                );
            })}
        </Box>
    );
};
