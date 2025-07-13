import { Route, Routes } from 'react-router-dom';
import { OtherSettingsCards } from '../components/OtherSettingsCards';
import { AIQueryPage } from '../pages/AIQueryPage';
import { IntegrationPage } from '../pages/IntegrationPage';
import { MetadataPage } from '../pages/MetadataPage';
import { NavigationPage } from '../pages/NavigationPage';
import { UserProfilePage } from '../pages/UserProfilePage';


export const AppRoutes = () => (
    <Routes>
        <Route path='/' element={<NavigationPage />} >
            <Route path='user' element={<UserProfilePage />} />
            <Route path='query' element={<AIQueryPage />} />
            <Route path='integrations' element={<IntegrationPage/>} />
            <Route path='metadata' element={<MetadataPage/>} />
            <Route path='othersettings' element={<OtherSettingsCards/>} />
        </Route>
        <Route path='/auth-callback' element={<div>Signing you in...</div>} />
    </Routes>
); 