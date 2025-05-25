import { AppRoutes } from './router/AppRoutes';
import { BrowserRouter } from 'react-router-dom';
import { AuthRedirectHandler } from './components/AuthRedirectHandler';

function App() {
    return (
        <BrowserRouter>
            <AuthRedirectHandler/>
            <AppRoutes/>
        </BrowserRouter>
    );
}
export default App;