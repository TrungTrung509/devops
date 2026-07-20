/**
 * Auth Guard - Protects routes requiring authentication.
 * Does NOT redirect during bootstrapping (waiting for /users/me).
 */

import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './AuthContext';

export default function AuthGuard() {
  const { isAuthenticated, isBootstrapping } = useAuth();

  // Still bootstrapping -> don't redirect, let AuthBootstrap show loading
  if (isBootstrapping) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
