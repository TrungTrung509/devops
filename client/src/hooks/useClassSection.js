/**
 * Class Section Query Hooks
 */

import { useQuery } from '@tanstack/react-query';
import { classSectionApi } from '@/services/classSectionApi';
import { QUERY_KEYS } from './useAuth';

export function useClassSectionsQuery(filters = {}) {
  return useQuery({
    queryKey: QUERY_KEYS.classSections(filters),
    queryFn: () => classSectionApi.getAll(filters),
    staleTime: 2 * 60 * 1000,
    select: (data) => {
      if (!data) return [];
      return Array.isArray(data) ? data : [];
    },
  });
}
