/**
 * Admin Guard - Protects admin routes for Admin role only.
 * Redirects non-Admins based on their role.
 */

import { Navigate } from 'react-router-dom';
import { getUserRole, ROLES } from '@/utils/auth';

export default function AdminGuard({ children }) {
  const role = getUserRole();

  if (role === ROLES.SINH_VIEN) {
    return <Navigate to="/student" replace />;
  }
  if (role === ROLES.GIANG_VIEN) {
    return <Navigate to="/teacher" replace />;
  }
  if (role !== ROLES.ADMIN) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
