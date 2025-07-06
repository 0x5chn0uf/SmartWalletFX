import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';

interface ProtectedRouteProps {
  children: React.ReactElement;
  roles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, roles }) => {
  const { isAuthenticated, status, user } = useSelector((state: RootState) => state.auth);

  const hasSessionFlag =
    typeof window !== 'undefined' && localStorage.getItem('session_active') === '1';

  if (status === 'loading' || (status === 'idle' && hasSessionFlag)) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login-register" replace />;
  }

  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

export default ProtectedRoute;
