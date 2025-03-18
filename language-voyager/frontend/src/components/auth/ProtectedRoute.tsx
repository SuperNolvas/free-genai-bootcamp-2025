import { Navigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { token, isLoading } = useSelector((state: RootState) => state.auth);
  const location = useLocation();

  // If authentication is still loading, you could show a loading spinner
  if (isLoading) {
    return <div>Loading...</div>;
  }

  // If not authenticated, redirect to login with return URL
  if (!token) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  // If authenticated, render children
  return <>{children}</>;
}