import { DatastoreCreationForm } from '@/features/integration/components/DatastoreCreationForm.tsx';
import { DatastoresList } from '@/features/integration/components/DatastoresList.tsx';


export const DatastorePage = () => {
    return (
        <div>
            <DatastoreCreationForm/>
            <DatastoresList/>
        </div>
    )
};