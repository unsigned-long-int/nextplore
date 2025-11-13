import {
    Box,
    Combobox,
    Divider,
    Group,
    InputBase,
    Text,
    Title,
    Transition,
    useCombobox
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {type ReactNode, useEffect, useMemo, useState} from 'react';
import {IconAtom, IconBrain, IconCloud, IconRobot, IconSparkles} from '@tabler/icons-react';

import { PromptBox } from '@/features/ai-query/components/PromptBox';
import { QueryStatementPreview } from '@/features/ai-query/components/QueryStatementPreview';
import { QueryResultTable } from '@/features/ai-query/components/QueryResultTable';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';
import { useGetModels } from '@/features/ai-query/hooks/useGetModels';
import { useGetAiResponse } from '@/features/ai-query/hooks/useGetAiResponse';
import type { ModelInfo } from '@/shared/api/services/ai-query/types.gen';


const modelIcons: Record<string, ReactNode> = {
    'moonshotai': <IconRobot size={16} />,
    'meta-llama': <IconBrain size={16} />,
    'qwen': <IconCloud size={16} />,
    'deepseek': <IconAtom size={16} />,
    'gpt-4o': <IconSparkles size={16} />,
    'default': <IconRobot size={16} />,
};

interface ModelOption {
    model_id: string;
    label: string;
    provider: string;
    icon?: ReactNode;
}

export const AiQueryPage = () => {
    const [prompt, setPrompt] = useState('');
    const [selectedModel, setSelectedModel] = useState<string | null>(null);
    const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
    const [search, setSearch] = useState('');
    const [aiQueryResponse, setAiQueryResponse] = useState<{ [key: string]: string }[]>([]);
    const [sqlPreview, setSqlPreview] = useState('');
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const {data = [], isError, isSuccess, error} = useGetModels();
    const getAiResponse = useGetAiResponse();

    const combobox = useCombobox({onDropdownClose: () => combobox.resetSelectedOption()});

    const modelOptions: ModelOption[] = useMemo(() => {
        return (data as ModelInfo[]).map((m) => ({
            provider: m.provider,
            model_id: m.model_id,
            label: `${m.label} (${m.tags.join(', ')})`,
            icon: modelIcons[m.model_id?.toLowerCase() ?? ''] ?? modelIcons.default,
        }));
    }, [data]);

    useEffect(() => {
        if (isSuccess && modelOptions.length > 0 && (!selectedModel || !selectedProvider)) {
            setSelectedModel(modelOptions[0].model_id);
            setSelectedProvider(modelOptions[0].provider);
            setSearch(modelOptions[0].label);
        }
    }, [isSuccess, modelOptions, selectedModel, selectedProvider]);

    useEffect(() => {
        if (isError) {
            const message = (error as { message?: string } | undefined)?.message ?? 'Models retrieval failed';
            setErrorMessage(message);
            notifications.show({
                color: 'red',
                title: 'Failed to load models',
                message,
                autoClose: 8000,
                withBorder: true,
            })
        }
    }, [isError, error])


    const filteredOptions = useMemo(() => {
        if (!search) return modelOptions;
        return modelOptions.filter((opt) => {
            opt.label.toLowerCase().includes(search.toLowerCase().trim());
        });
    }, [modelOptions, search]);

    const handleSelectModel = (modelId: string) => {
        const selected = modelOptions.find((opt) => opt.model_id === modelId);
        if (!selected) return;

        setSelectedModel(modelId);
        setSelectedProvider(selected.provider);
        setSearch(selected.label);
        combobox.closeDropdown();
    };

    const handleAiQueryRequest = async () => {
        if (!selectedModel || !selectedProvider) return;

        setErrorMessage(null);
        setSqlPreview('');
        setAiQueryResponse([]);

        try {
            const response = await getAiResponse.mutateAsync({
                provider: selectedProvider,
                model_id: selectedModel,
                prompt,
            });
            setAiQueryResponse(response.data);
            setSqlPreview(response.sql);
        } catch (e: any) {
            console.error(e);
            setErrorMessage(e.message);
        }
    };

    const loading = getAiResponse.isPending;

    return (
        <Box>
            <Title order={2} mb='xs'>
                Request any data from database
            </Title>
            <Text c='dimmed' size='sm' mb='md'>
                Example: "Total number characters in marvel movies?"
            </Text>
            <Box w={400} mb="md">
                <Combobox
                    store={combobox}
                    withinPortal={false}
                    onOptionSubmit={handleSelectModel}
                >
                    <Combobox.Target>
                        <InputBase
                            label='Choose LLM Model'
                            value={search}
                            onChange={(event) => {
                                const val = event.currentTarget.value;
                                setSearch(val);
                                combobox.openDropdown();
                                combobox.updateSelectedOptionIndex();
                            }}
                            onClick={() => combobox.openDropdown()}
                            onFocus={() => combobox.openDropdown()}
                            onBlur={() => {
                                combobox.closeDropdown();
                                const selected = modelOptions.find((opt) => opt.model_id === selectedModel);
                                setSearch(selected?.label ?? '');
                            }}
                            placeholder='Search model'
                            rightSection={<Combobox.Chevron/>}
                            rightSectionPointerEvents='none'
                            withAsterisk
                        />
                    </Combobox.Target>
                    <Combobox.Dropdown>
                        <Combobox.Options>
                            {filteredOptions.length > 0 ? (
                                filteredOptions.map((opt) => (
                                    <Combobox.Option key={opt.model_id} value={opt.model_id}>
                                        <Group gap='xs'>
                                            {opt.icon}
                                            <Text size='sm'>{opt.label}</Text>
                                        </Group>
                                    </Combobox.Option>
                                ))
                            ) : (
                                <Combobox.Empty>Nothing found</Combobox.Empty>
                            )}
                        </Combobox.Options>
                    </Combobox.Dropdown>
                </Combobox>
            </Box>
            <PromptBox
                prompt={prompt}
                setPrompt={setPrompt}
                onSubmit={handleAiQueryRequest}
                loading={loading}
            />
            {errorMessage && (
                <Box my='sm'>
                    <Text c='red' size='sm' ta='center'>
                        {errorMessage}
                    </Text>
                </Box>
            )}

            <Divider my='lg'/>
            <Box
                pos='relative'
                mih={260}
                style={{overflow: 'hidden'}}
            >
                {loading && (
                    <LoadingOverlay loadingText='Asking the model... LLM snail is inspecting it...' />
                )}

                <Transition mounted={!loading && !!sqlPreview} transition='fade' duration={400}>
                    {(styles) => (
                        <div style={styles}>
                            <QueryStatementPreview sql={sqlPreview} />
                            <QueryResultTable data={aiQueryResponse} />
                        </div>
                    )}
                </Transition>
            </Box>
        </Box>
    )
};
