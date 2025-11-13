import { CreationForm } from '@/features/integration/components/CreationForm';
import { IntegrationsList } from '@/features/integration/components/IntegrationsList';


export const IntegrationPage = () => {
    return (
        <div>
            <CreationForm/>
            <IntegrationsList/>
        </div>
    )
};