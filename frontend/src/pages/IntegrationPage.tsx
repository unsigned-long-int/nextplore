import { Group } from '@mantine/core'
import { CreateIntegrationButton } from '../components/CreateIntegrationButton'
import { IntegrationsList } from '../components/IntegrationsList'

export const IntegrationPage = () => {
    return (
    <div>
        <Group wrap="wrap">
            <CreateIntegrationButton/>
            <IntegrationsList/>
        </Group>
    </div>
    )
}