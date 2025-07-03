import { Routes, Route, Navigate, BrowserRouter } from 'react-router-dom';
import { NavigationPage } from '../pages/NavigationPage';
import { QueryPage } from '../pages/QueryPage';
import { AIQueryPage } from '../pages/AIQueryPage';
import { UserProfilePage } from '../pages/UserProfilePage';
import { IntegrationPage } from '../pages/IntegrationPage';


export const AppRoutes = () => (
    <Routes>
        <Route path='/' element={<NavigationPage />} >
            <Route path='user' element={<UserProfilePage />} />
            <Route path='query' element={<AIQueryPage />} />
            <Route path='integrations' element={<IntegrationPage/>} />
        </Route>
        <Route path='/auth-callback' element={<div>Signing you in...</div>} />
    </Routes>
); 