/**
 * Semester API - CRUD for semesters (Admin only for writes)
 * Backend returns paginated: { status, success, message, data: { items: Semester[], total: int } }
 * apiClient interceptor unwraps to: response.data = { items: [], total: ... }
 */

import apiClient from '@/services/apiClient';

export const semesterApi = {
  getAll: async (params = {}) => {
    const response = await apiClient.get('/semesters/', { params });
    return response.data;
  },

  getById: async (MaHocKy) => {
    const response = await apiClient.get(`/semesters/${MaHocKy}`);
    return response.data;
  },

  create: async (data) => {
    const response = await apiClient.post('/semesters/', data);
    return response.data;
  },

  update: async (MaHocKy, data) => {
    const response = await apiClient.put(`/semesters/${MaHocKy}`, data);
    return response.data;
  },

  delete: async (MaHocKy) => {
    const response = await apiClient.delete(`/semesters/${MaHocKy}`);
    return response.data;
  },
};
