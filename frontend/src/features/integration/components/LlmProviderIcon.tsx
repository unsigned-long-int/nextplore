import {siAnthropic, siMeta, siHuggingface, siMistralai, siOllama, siGooglegemini} from 'simple-icons';
import type { SimpleIcon } from 'simple-icons';
import { IconBrain } from '@tabler/icons-react';

const OPENAI_SVG = `<path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729z"/>`;

const COHERE_SVG = `<circle cx="8" cy="10" r="3" /><circle cx="16" cy="10" r="3" /><circle cx="12" cy="16" r="3" />`;

const DEEPSEEK_SVG = `<path d="M23.748 4.482c-.254-.124-.364.113-.512.234-.051.039-.094.09-.137.136-.372.397-.806.657-1.373.626-.829-.046-1.537.214-2.163.848-.133-.782-.575-1.248-1.247-1.548-.352-.156-.708-.311-.955-.65-.172-.241-.219-.51-.305-.774-.055-.16-.11-.323-.293-.35-.2-.031-.278.136-.356.276-.313.572-.434 1.202-.422 1.84.027 1.436.633 2.58 1.838 3.393.137.093.172.187.129.323-.082.28-.18.552-.266.833-.055.179-.137.217-.329.14a5.526 5.526 0 01-1.736-1.18c-.857-.828-1.631-1.742-2.597-2.458a11.365 11.365 0 00-.689-.471c-.985-.957.13-1.743.388-1.836.27-.098.093-.432-.779-.428-.872.004-1.67.295-2.687.684a3.055 3.055 0 01-.465.137 9.597 9.597 0 00-2.883-.102c-1.885.21-3.39 1.102-4.497 2.623C.082 8.606-.231 10.684.152 12.85c.403 2.284 1.569 4.175 3.36 5.653 1.858 1.533 3.997 2.284 6.438 2.14 1.482-.085 3.133-.284 4.994-1.86.47.234.962.327 1.78.397.63.059 1.236-.03 1.705-.128.735-.156.684-.837.419-.961-2.155-1.004-1.682-.595-2.113-.926 1.096-1.296 2.746-2.642 3.392-7.003.05-.347.007-.565 0-.845-.004-.17.035-.237.23-.256a4.173 4.173 0 001.545-.475c1.396-.763 1.96-2.015 2.093-3.517.02-.23-.004-.467-.247-.588zM11.581 18c-2.089-1.642-3.102-2.183-3.52-2.16-.392.024-.321.471-.235.763.09.288.207.486.371.739.114.167.192.416-.113.603-.673.416-1.842-.14-1.897-.167-1.361-.802-2.5-1.86-3.301-3.307-.774-1.393-1.224-2.887-1.298-4.482-.02-.386.093-.522.477-.592a4.696 4.696 0 011.529-.039c2.132.312 3.946 1.265 5.468 2.774.868.86 1.525 1.887 2.202 2.891.72 1.066 1.494 2.082 2.48 2.914.348.292.625.514.891.677-.802.09-2.14.11-3.054-.614zm1-6.44a.306.306 0 01.415-.287.302.302 0 01.2.288.306.306 0 01-.31.307.303.303 0 01-.304-.308zm3.11 1.596c-.2.081-.399.151-.59.16a1.245 1.245 0 01-.798-.254c-.274-.23-.47-.358-.552-.758a1.73 1.73 0 01.016-.588c.07-.327-.008-.537-.239-.727-.187-.156-.426-.199-.688-.199a.559.559 0 01-.254-.078c-.11-.054-.2-.19-.114-.358.028-.054.16-.186.192-.21.356-.202.767-.136 1.146.016.352.144.618.408 1.001.782.391.451.462.576.685.914.176.265.336.537.445.848.067.195-.019.354-.25.452z""/>`;


type ProviderConfig = {
    patterns: string[];
    urlPatterns?: string[];
    icon?: SimpleIcon;
    svg?: string;
    color: string;
};

const PROVIDER_PATTERNS: ProviderConfig[] = [
    {
        patterns: ['huggingface', 'hf/'],
        urlPatterns: ['huggingface', 'hf.co'],
        icon: siHuggingface,
        color: `#${siHuggingface.hex}`,
    },
    {
        patterns: ['gpt', 'openai', 'o1', 'o3', 'davinci', 'turbo'],
        svg: OPENAI_SVG,
        color: '#10a37f',
    },
    {
        patterns: ['ollama'],
        icon: siOllama,
        color: `#A8FF47`,
    },
    {
        patterns: ['claude', 'anthropic', 'sonnet', 'haiku', 'opus'],
        icon: siAnthropic,
        color: `#E0E0E0`,
    },
    {
        patterns: ['llama', 'meta', 'codellama'],
        icon: siMeta,
        color: `#${siMeta.hex}`,
    },
    {
        patterns: ['mistral', 'mixtral', 'codestral'],
        icon: siMistralai,
        color: `#${siMistralai.hex}`,
    },
    {
        patterns: ['gemini', 'gemma', 'google', 'palm'],
        icon: siGooglegemini,
        color: `#${siGooglegemini.hex}`,
    },
    {
        patterns: ['command', 'cohere'],
        svg: COHERE_SVG,
        color: '#39594D',
    },
    {
        patterns: ['deepseek'],
        svg: DEEPSEEK_SVG,
        color: '#4169E1',
    },
];

const findProvider = (modelId: string, apiBase?: string) => {
    return PROVIDER_PATTERNS.find(({ patterns, urlPatterns }) => {
        const lower = modelId.toLowerCase();
        const baseMatch = apiBase
            ? urlPatterns?.some((p) => apiBase.toLowerCase().includes(p))
            : false;
        return baseMatch || patterns.some((p) => lower.includes(p));
    });
};


export const LlmProviderIcon = ({ modelId, apiBase, size = 16 }: { modelId: string; apiBase?: string, size?: number }) => {
    const match = findProvider(modelId, apiBase);

    if (!match) return <IconBrain size={size} color='#9C9C9C' />;

    if (match.icon) {
        return (
            <svg
                width={size}
                height={size}
                viewBox='0 0 24 24'
                fill={match.color}
                dangerouslySetInnerHTML={{ __html: match.icon.svg }}
            />
        );
    }

    return (
        <svg
            width={size}
            height={size}
            viewBox='0 0 24 24'
            fill={match.color}
            dangerouslySetInnerHTML={{ __html: match.svg! }}
        />
    );
};

export const getLlmProviderColor = (modelId: string, apiBase?: string): string => {
    return findProvider(modelId, apiBase)?.color ?? '#9C9C9C';
};