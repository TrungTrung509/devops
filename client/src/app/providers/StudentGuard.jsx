/**
 * StudentGuard - Protects routes requiring SinhVien role.
 * Uses synchronous JWT decode to avoid redirect loops during bootstrap.
 * Redirects non-students back to their appropriate portal or login.
 */

import { Navigate } from 'react-router-dom';
import { getUserRole, ROLES } from '@/utils/auth';

export default function StudentGuard({ children }) {
  const role = getUserRole();

  if (role === ROLES.SINH_VIEN) {
    return children;
  }
  if (role === ROLES.GIANG_VIEN) {
    return <Navigate to="/teacher" replace />;
  }
  if (role === ROLES.ADMIN) {
    return <Navigate to="/admin" replace />;
  }
  return <Navigate to="/login" replace />;
}
