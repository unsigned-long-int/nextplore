import { IconCheck, IconCopy } from '@tabler/icons-react';
import { Button, Tooltip } from '@mantine/core';
import { useClipboard } from '@mantine/hooks';

export const QueryStatementCopyButton = ({ sql }: { sql: string })=> {
    const clipboard = useClipboard({ timeout: 1000 });
    return (
        <Tooltip
            label='Query copied!'
            offset={5}
            position='bottom'
            radius='xl'
            transitionProps={{ duration: 100, transition: 'slide-down' }}
            opened={clipboard.copied}
        >
            <Button
                variant='light'
                rightSection={
                clipboard.copied ? (
                    <IconCheck size={16} stroke={1.5} />
                ) : (
                    <IconCopy size={16} stroke={1.5} />
                )
                }
                radius='xl'
                size='sm'
                pr={10}
                h={40}
                styles={{ section: { marginLeft: 22 } }}
                onClick={() => clipboard.copy(sql)}
            >
                Copy query to clipboard
            </Button>
        </Tooltip>
    );
};