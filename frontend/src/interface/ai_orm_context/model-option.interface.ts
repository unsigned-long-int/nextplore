import type { ReactNode } from 'react';


export interface ModelOption {
    model_id: string;
    label: string;
    provider: string;
    icon?: ReactNode;
}