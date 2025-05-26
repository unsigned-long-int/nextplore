import { Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { QueryPage } from './pages/QueryPage';
import { UserProfilePage } from './pages/UserProfilePage';

export const App = () => (
    <Routes>
        <Route path='/' element={<HomePage />} />
            <Route path='querypage' element={<QueryPage />} />
            <Route path='user' element={<UserProfilePage />} />
        <Route path='/auth-callback' element={<div>Signing you in...</div>} />
    </Routes>
);

export default App;