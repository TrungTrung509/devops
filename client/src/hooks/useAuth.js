/**
 * Auth Query Hooks
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi, tokenStorage } from '@/services/authApi';
import { getUserRole, getRedirectPath } from '@/utils/auth';
import { userApi } from '@/services/userApi';

export const QUERY_KEYS = {
  currentUser: ['currentUser'],
  classSections: (filters) => ['classSections', filters],
  enrollmentHistory: (maHocKy) => ['enrollmentHistory', maHocKy],
  branches: ['branches'],
  semesters: ['semesters'],
};


// useLoginMutation

export function useLoginMutation(options = {}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ username, password }) => authApi.login(username, password),
    onSuccess: async (data) => {
      // 1. Save tokens
      tokenStorage.setTokens(data);

      // 2. Decode role from JWT immediately (no API call)
      const role = getUserRole();

      // 3. Fetch user profile using the new token
      let user = null;
      try {
        user = await userApi.getCurrentUser();
      } catch (err) {
        // If /users/me fails, navigate anyway based on role from token
      }

      // 4. Store user in React Query cache so AuthBootstrap finds it
      if (user) {
        queryClient.setQueryData(QUERY_KEYS.currentUser, user);
      }

      // 5. Call custom onSuccess if provided
      if (options.onSuccess) {
        options.onSuccess({ ...data, role, user });
      }

      // 6. Navigate to appropriate page based on role
      const redirectPath = getRedirectPath(role);
      navigate(redirectPath, { replace: true });
    },
    onError: (error) => {
      if (options.onError) {
        options.onError(error);
      }
    },
  });
}


// useLogoutMutation

export function useLogoutMutation() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const refreshToken = tokenStorage.getRefreshToken();
      try {
        await authApi.logout(refreshToken);
      } catch {
        // Ignore logout API errors
      }
    },
    onSettled: () => {
      tokenStorage.clearTokens();
      queryClient.clear();
      navigate('/login', { replace: true });
    },
  });
}


// useCurrentUserQuery

export function useCurrentUserQuery(options = {}) {
  return useQuery({
    queryKey: QUERY_KEYS.currentUser,
    queryFn: () => userApi.getCurrentUser(),
    retry: 1,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}
