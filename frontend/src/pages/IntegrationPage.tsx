import { CreateIntegrationButton } from '../components/integrations/CreateIntegrationButton';
import { IntegrationsList } from '../components/integrations/IntegrationList';


export const IntegrationPage = () => {
    return (
        <div>
            <CreateIntegrationButton/>
            <IntegrationsList/>
        </div>
    )
};