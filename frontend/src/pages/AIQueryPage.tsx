import {
    Box,
    Combobox,
    Divider,
    Group,
    InputBase,
    Loader,
    Text,
    Title,
    Transition,
    useCombobox,
} from '@mantine/core';
import { useEffect, useMemo, useState } from 'react';
import { PromptBox } from '../components/ai_queries/PromptBox';
import { QueryPreview } from '../components/ai_queries/QueryPreview';
import { ResultTable } from '../components/ai_queries/ResultTable';
  
import { useAIGenerativeModels } from '../hooks/useAIGenerativeModels';
import { useAIQueryRequest } from '../hooks/useAIQueryRequest';
import { getModelIcon } from '../icons/modelsIcons';
  
import type { ModelInfo } from '../interface/ai-generative-models-response.interface';
import type { AIQueryRequest } from '../interface/ai-query-request.interface';
import type { ModelOption } from '../interface/model-option.interface';
  
export const AIQueryPage = () => {
const [prompt, setPrompt] = useState('');
const [selectedModel, setSelectedModel] = useState<string | null>(null);
const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
const [modelOptions, setModelOptions] = useState<ModelOption[]>([]);
const [search, setSearch] = useState('');
const [aiQueryResponse, setAIQueryResponse] = useState<{ [key: string]: string }[]>([]);
const [sqlPreview, setSqlPreview] = useState('');
const [querying, setQuerying] = useState(false);
const [errorMessage, setErrorMessage] = useState<string | null>(null);

const { getAIQueryResponse } = useAIQueryRequest();
const { getAIGenerativeModels } = useAIGenerativeModels();
const combobox = useCombobox({ onDropdownClose: () => combobox.resetSelectedOption() });

useEffect(() => {
    getAIGenerativeModels().then((models) => {
    const options = models.map((m: ModelInfo) => ({
        provider: m.provider,
        model_id: m.model_id,
        label: `${m.label} (${m.tags.join(', ')})`,
        icon: getModelIcon(m.model_id),
    }));
    setModelOptions(options);
    if (options.length > 0) {
        setSelectedModel(options[0].model_id);
        setSelectedProvider(options[0].provider);
        setSearch(options[0].label);
    }
    });
}, []);

const filteredOptions = useMemo(() => {
    if (!search) return modelOptions;
    return modelOptions.filter((opt) =>
    opt.label.toLowerCase().includes(search.toLowerCase().trim())
    );
}, [modelOptions, search]);

const handleSelectModel = (modelId: string) => {
    const selected = modelOptions.find((opt) => opt.model_id === modelId);
    if (!selected) return;

    setSelectedModel(modelId);
    setSelectedProvider(selected.provider);
    setSearch(selected.label);
    combobox.closeDropdown();
};

const handleAIQueryRequest = async () => {
    if (!selectedModel || !selectedProvider) return;

    setQuerying(true);
    setAIQueryResponse([]);
    setSqlPreview('');
    setErrorMessage(null);

    try {
    const request: AIQueryRequest = {
        provider: selectedProvider,
        model_id: selectedModel,
        prompt,
    };
    const response = await getAIQueryResponse(request);
    setAIQueryResponse(response.data);
    setSqlPreview(response.sql);
    } catch (e: any) {
    console.error(e);
    setErrorMessage(e.message);
    } finally {
    setQuerying(false);
    }
};

return (
    <Box>
    <Title order={2} mb="xs">
        Request any data from database
    </Title>
    <Text c="dimmed" size="sm" mb="md">
        Example: "Total number of employees in german payroll"
    </Text>
    <Box w={400} mb="md">
        <Combobox
        store={combobox}
        withinPortal={false}
        onOptionSubmit={handleSelectModel}
        >
            <Combobox.Target>
                <InputBase
                label="Choose LLM Model"
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
                placeholder="Search model"
                rightSection={<Combobox.Chevron />}
                rightSectionPointerEvents="none"
                withAsterisk
                />
            </Combobox.Target>
            <Combobox.Dropdown>
                <Combobox.Options>
                {filteredOptions.length > 0 ? (
                    filteredOptions.map((opt) => (
                    <Combobox.Option key={opt.model_id} value={opt.model_id}>
                        <Group gap="xs">
                        {opt.icon}
                        <Text size="sm">{opt.label}</Text>
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
        onSubmit={handleAIQueryRequest}
        loading={querying}
    />

    {errorMessage && (
        <Box my="sm">
        <Text c="red" size="sm" ta="center">
            {errorMessage}
        </Text>
        </Box>
    )}

    <Divider my="lg" />
    {querying && <Loader variant="bars" />}
    <Transition mounted={!querying && !!sqlPreview} transition="fade" duration={400}>
        {(styles) => (
        <div style={styles}>
            <QueryPreview sql={sqlPreview} />
            <ResultTable data={aiQueryResponse} />
        </div>
        )}
    </Transition>
    </Box>
);
};
