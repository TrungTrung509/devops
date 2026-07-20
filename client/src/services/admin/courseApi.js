/**
 * Course API - CRUD for courses (Admin only for writes)
 * Backend returns paginated: { status, success, message, data: { items: Course[], total: int } }
 * apiClient interceptor unwraps to: response.data = { items: [], total: ... }
 */

import apiClient from '@/services/apiClient';

export const courseApi = {
  getAll: async (params = {}) => {
    const response = await apiClient.get('/courses/', { params });
    return response.data;
  },

  getById: async (MaHocPhan) => {
    const response = await apiClient.get(`/courses/${MaHocPhan}`);
    return response.data;
  },

  create: async (data) => {
    const response = await apiClient.post('/courses/', data);
    return response.data;
  },

  update: async (MaHocPhan, data) => {
    const response = await apiClient.put(`/courses/${MaHocPhan}`, data);
    return response.data;
  },

  delete: async (MaHocPhan) => {
    const response = await apiClient.delete(`/courses/${MaHocPhan}`);
    return response.data;
  },

  getReplicationStatus: async () => {
    const response = await apiClient.get('/courses/replication/status');
    return response.data;
  },

  triggerReplication: async () => {
    const response = await apiClient.post('/courses/replication/recover');
    return response.data;
  },
};
