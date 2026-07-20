/**
 * Admin Overview API - Thong ke tong quan cho cac module Admin
 * Backend: GET /reports/admin-overview/{entity}
 * Entity: teachers | students | courses | semesters | classrooms | class-sections
 */

import apiClient from '@/services/apiClient';

export const overviewApi = {
  /**
   * GET /reports/admin-overview/{entity}
   * Response: AdminOverviewResponse
   */
  getOverview: async (entity) => {
    const response = await apiClient.get(`/reports/admin-overview/${entity}`);
    return response.data;
  },
};

/**
 * Query key factory for admin overview
 */
export const overviewKeys = {
  all: ['admin', 'overview'],
  entity: (entity) => ['admin', 'overview', entity],
};
