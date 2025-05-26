import { Routes, Route, Navigate, BrowserRouter } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { HomePage } from '../pages/HomePage';
import { QueryPage } from '../pages/QueryPage';
import { UserProfilePage } from '../pages/UserProfilePage';
import { AppLayout } from '../components/AppLayout';

export const AppRoutes = () => (
    <BrowserRouter>
        <Routes>
            <Route path='/' element={<HomePage />} />
            <Route path='querypage' element={<ProtectedRoute><QueryPage /></ProtectedRoute>} />
            <Route path='user' element={<ProtectedRoute><UserProfilePage /></ProtectedRoute>} />
            <Route path='/auth-callback' element={<div>Signing you in...</div>} />
        </Routes>
  </BrowserRouter>
);

export default App;