import { Routes, Route } from 'react-router-dom';
import { HomePage } from '../pages/HomePage';
import { QueryPage } from '../pages/QueryPage'
import { ProtectedRoute } from '../components/ProtectedRoute';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route
        path="/querypage"
        element={
          <ProtectedRoute>
            <QueryPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};