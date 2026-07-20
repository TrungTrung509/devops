/**
 * AuthBootstrap - Fetches user profile and stores in AuthContext on app load.
 * Shows a loading overlay while bootstrapping. Handles 401 gracefully.
 * Note: Does NOT use useNavigate — must stay outside <Router> context.
 */

import { useEffect } from 'react';
import { useAuth } from './AuthContext';
import { useCurrentUserQuery } from '@/hooks/useUser';
import { tokenStorage } from '@/services/authApi';
import { Spin } from 'antd';

export default function AuthBootstrap({ children }) {
  const { setUserData, clearUser, setIsBootstrapping } = useAuth();

  const hasToken = !!tokenStorage.getAccessToken();

  const { data: user, isLoading, isError, error } = useCurrentUserQuery({
    enabled: hasToken,
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    if (hasToken) {
      setIsBootstrapping(true);
    }
  }, [hasToken, setIsBootstrapping]);

  useEffect(() => {
    if (isLoading) {
      setIsBootstrapping(true);
      return;
    }

    if (isError) {
      // 401 or other fetch error -> clear session
      if (error?.isAuthError || error?.status === 401) {
        tokenStorage.clearTokens();
        clearUser();
      }
      setIsBootstrapping(false);
      return;
    }

    if (user) {
      setUserData(user);
    } else {
      clearUser();
    }
    setIsBootstrapping(false);
  }, [user, isLoading, isError, error, setUserData, clearUser, setIsBootstrapping]);

  // While bootstrapping with a token, show loading overlay
  if (hasToken && isLoading) {
    return (
      <div style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f2f5',
        zIndex: 9999,
      }}>
        <Spin size="large" tip="Đang tải thông tin..." />
      </div>
    );
  }

  return children;
}
