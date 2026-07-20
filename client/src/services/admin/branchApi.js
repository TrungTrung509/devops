/**
 * Branch API - CRUD for campuses/branches (Admin only for writes)
 * Backend returns: { status, success, message, data: Branch[] }
 * apiClient interceptor unwraps to: response.data = Branch[]
 */

import apiClient from '@/services/apiClient';

export const branchApi = {
  getAll: async () => {
    const response = await apiClient.get('/branches/');
    return response.data;
  },

  getById: async (MaCoSo) => {
    const response = await apiClient.get(`/branches/${MaCoSo}`);
    return response.data;
  },

  create: async (data) => {
    const response = await apiClient.post('/branches/', data);
    return response.data;
  },

  update: async (MaCoSo, data) => {
    const response = await apiClient.put(`/branches/${MaCoSo}`, data);
    return response.data;
  },

  delete: async (MaCoSo) => {
    const response = await apiClient.delete(`/branches/${MaCoSo}`);
    return response.data;
  },
};
