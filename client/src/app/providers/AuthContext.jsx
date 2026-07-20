/**
 * Auth Context - Global auth state for role-based access control
 * Provides: user, isBootstrapping, isAuthenticated, role helpers
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { tokenStorage } from '@/services/authApi';
import { normalizeRole, ROLES } from '@/utils/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(false);

  const setUserData = useCallback((userData) => {
    setUser(userData || null);
    setIsBootstrapping(false);
  }, []);

  const clearUser = useCallback(() => {
    setUser(null);
    setIsBootstrapping(false);
  }, []);

  const startBootstrap = useCallback(() => {
    setIsBootstrapping(true);
  }, []);

  // Derived values from user object
  const role = user?.role ? normalizeRole(user.role) : null;
  const isAdmin = role === ROLES.ADMIN;
  const isStudent = role === ROLES.SINH_VIEN;
  const isTeacher = role === ROLES.GIANG_VIEN;

  // isAuthenticated: token exists (checked synchronously, no API needed)
  const isAuthenticated = tokenStorage.isAuthenticated();

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        setUserData,
        clearUser,
        startBootstrap,
        isBootstrapping,
        setIsBootstrapping,
        isAuthenticated,
        isAdmin,
        isStudent,
        isTeacher,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
