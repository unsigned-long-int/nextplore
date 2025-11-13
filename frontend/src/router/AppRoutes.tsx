import { Route, Routes } from 'react-router-dom';

import { AiQueryPage } from '@/features/ai-query/pages/AiQueryPage';
import { IntegrationPage } from '@/features/integration/pages/IntegrationPage';
import { UserProfilePage } from '@/features/user/pages/UserProfilePage';
import { MetaPage } from '@/features/meta/pages/MetaPage';
import { NavigationPage } from '@/features/navigation/pages/NavigationPage';


export const AppRoutes = () => (
    <Routes>
        <Route path='/' element={<NavigationPage />} >
            <Route path='user' element={<UserProfilePage />} />
            <Route path='query' element={<AiQueryPage />} />
            <Route path='integrations' element={<IntegrationPage/>} />
            <Route path='metadata' element={<MetaPage/>} />
        </Route>
        <Route path='/auth-callback' element={<div>Signing you in...</div>} />
    </Routes>
); 