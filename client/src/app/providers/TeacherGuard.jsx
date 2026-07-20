/**
 * TeacherGuard - Protects routes requiring GiangVien role.
 * Uses synchronous JWT decode to avoid redirect loops during bootstrap.
 * Redirects non-teachers back to their appropriate portal or login.
 */

import { Navigate } from 'react-router-dom';
import { getUserRole, ROLES } from '@/utils/auth';

export default function TeacherGuard({ children }) {
  const role = getUserRole();

  if (role === ROLES.GIANG_VIEN) {
    return children;
  }
  if (role === ROLES.SINH_VIEN) {
    return <Navigate to="/student" replace />;
  }
  if (role === ROLES.ADMIN) {
    return <Navigate to="/admin" replace />;
  }
  return <Navigate to="/login" replace />;
}
