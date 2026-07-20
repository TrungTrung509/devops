/**
 * User Query Hooks
 */

import { useQuery } from '@tanstack/react-query';
import { userApi } from '@/services/userApi';
import { QUERY_KEYS } from './useAuth';

export function useCurrentUserQuery(options = {}) {
  return useQuery({
    queryKey: QUERY_KEYS.currentUser,
    queryFn: () => userApi.getCurrentUser(),
    retry: 1,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}
