import {
    IconAtom,
    IconBrain,
    IconCloud,
    IconRobot,
    IconSparkles
} from '@tabler/icons-react';
import type { ReactNode } from 'react';
  

export const modelIcons: Record<string, ReactNode> = {
    'moonshotai': <IconRobot size={16} />,
    'meta-llama': <IconBrain size={16} />,
    'qwen': <IconCloud size={16} />,
    'deepseek': <IconAtom size={16} />,
    'gpt-4o': <IconSparkles size={16} />,
    'default': <IconRobot size={16} />,
};

export const getModelIcon = (model_id?: string): ReactNode =>
modelIcons[model_id?.toLowerCase() ?? ''] ?? modelIcons.default;