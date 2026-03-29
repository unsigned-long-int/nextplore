import { LlmCreationForm } from '@/features/integration/components/LlmCreationForm.tsx';
import { LlmList } from '@/features/integration/components/LlmList.tsx';


export const LlmPage = () => {
    return (
        <div>
            <LlmCreationForm/>
            <LlmList/>
        </div>
    )
};