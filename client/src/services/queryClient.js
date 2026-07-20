/**
 * QueryClient configuration for @tanstack/react-query
 */

import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      throwOnError: false,
    },
    mutations: {
      throwOnError: false,
    },
  },
});

export default queryClient;
