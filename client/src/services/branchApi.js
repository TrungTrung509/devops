/**
 * Branch API - List of campuses/branches
 */

import apiClient from './apiClient';

/**
 * GET /branches/
 * Response: BranchResponse[]
 * BranchResponse: { maCoSo, tenCoSo, diaChi, soDienThoai, email, ngayThanhLap, trangThai, ngayTao }
 */
export const branchApi = {
  getAll: async () => {
    const response = await apiClient.get('/branches/');
    return response.data;
  },

  getById: async (branchId) => {
    const response = await apiClient.get(`/branches/${branchId}`);
    return response.data;
  },
};
