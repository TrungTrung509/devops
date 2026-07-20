/**
 * Branch and Semester Query Hooks
 */

import { useQuery } from '@tanstack/react-query';
import { branchApi } from '@/services/branchApi';
import { semesterApi } from '@/services/semesterApi';
import { QUERY_KEYS } from './useAuth';

export function useBranchesQuery() {
  return useQuery({
    queryKey: QUERY_KEYS.branches,
    queryFn: branchApi.getAll,
    staleTime: 30 * 60 * 1000,
    select: (data) => (Array.isArray(data) ? data : []),
  });
}

export function useSemestersQuery() {
  return useQuery({
    queryKey: QUERY_KEYS.semesters,
    queryFn: semesterApi.getAll,
    staleTime: 30 * 60 * 1000,
    select: (data) => (Array.isArray(data) ? data : []),
  });
}
