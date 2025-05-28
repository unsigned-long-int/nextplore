import { Routes, Route } from 'react-router-dom';
import { QueryPage } from './pages/QueryPage';
import { UserProfilePage } from './pages/UserProfilePage';
import { NavigationPage } from './pages/NavigationPage';

export const App = () => (
    <Routes>
        <Route path='/' element={<NavigationPage />} >
            <Route path='user' element={<UserProfilePage />} />
            <Route path='query' element={<QueryPage />} />
        </Route>
        <Route path='/auth-callback' element={<div>Signing you in...</div>} />
    </Routes>
);

export default App;