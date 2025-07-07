import { Routes, Route } from 'react-router-dom';
import { NavigationPage } from '../pages/NavigationPage';
import { AIQueryPage } from '../pages/AIQueryPage';
import { UserProfilePage } from '../pages/UserProfilePage';
import { IntegrationPage } from '../pages/IntegrationPage';
import { MetadataPage } from '../pages/MetadataPage';
import { OtherSettingsCards } from '../components/otherSettingsCards';


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