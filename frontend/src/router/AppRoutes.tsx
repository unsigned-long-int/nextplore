import { Route, Routes } from 'react-router-dom';

import { AiQueryPage } from '@/features/ai-query/pages/AiQueryPage';
import { DatastorePage } from '@/features/integration/pages/DatastorePage.tsx';
import { UserProfilePage } from '@/features/user/pages/UserProfilePage';
import { MetaPage } from '@/features/meta/pages/MetaPage';
import { NavigationPage } from '@/features/navigation/pages/NavigationPage';
import {LlmPage} from "@/features/integration/pages/LlmPage.tsx";


export const AppRoutes = () => (
    <Routes>
        <Route path='/' element={<NavigationPage />} >
            <Route path='user' element={<UserProfilePage />} />
            <Route path='query' element={<AiQueryPage />} />
            <Route path='llm' element={<LlmPage />} />
            <Route path='datastores' element={<DatastorePage/>} />
            <Route path='metadata' element={<MetaPage/>} />
        </Route>
        <Route path='/auth-callback' element={<div>Signing you in...</div>} />
    </Routes>
); 