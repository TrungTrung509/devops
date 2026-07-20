/**
 * Hook su dung admin overview API
 */

import { useQuery } from '@tanstack/react-query';
import { overviewApi, overviewKeys } from '@/services/admin/overviewApi';

/**
 * Lay thong ke tong quan cho mot entity
 * @param {string} entity - ten entity: teachers | students | courses | semesters | classrooms | class-sections
 * @param {object} options - React Query options
 */
export function useAdminEntityOverview(entity, options = {}) {
  return useQuery({
    queryKey: overviewKeys.entity(entity),
    queryFn: () => overviewApi.getOverview(entity),
    enabled: !!entity,
    staleTime: 30 * 1000,
    ...options,
  });
}
