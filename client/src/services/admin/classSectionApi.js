/**
 * Class Section API - CRUD for class sections + schedules (Admin only for writes)
 * Backend returns paginated for list: { status, success, message, data: { items: Section[], total: int } }
 * apiClient interceptor unwraps to: response.data = { items: [], total: ... }
 */

import apiClient from '@/services/apiClient';

export const classSectionApi = {
  getAll: async (params = {}) => {
    const response = await apiClient.get('/class-sections', { params });
    return response.data;
  },

  getById: async (MaLopHP) => {
    const response = await apiClient.get(`/class-sections/${MaLopHP}`);
    return response.data;
  },

  create: async (data) => {
    const response = await apiClient.post('/class-sections/', data);
    return response.data;
  },

  update: async (MaLopHP, data) => {
    const response = await apiClient.put(`/class-sections/${MaLopHP}`, data);
    return response.data;
  },

  delete: async (MaLopHP) => {
    const response = await apiClient.delete(`/class-sections/${MaLopHP}`);
    return response.data;
  },

  getSchedules: async (MaLopHP) => {
    const response = await apiClient.get(`/class-sections/${MaLopHP}/schedules`);
    return response.data;
  },

  addSchedule: async (MaLopHP, data) => {
    const response = await apiClient.post(`/class-sections/${MaLopHP}/schedules`, data);
    return response.data;
  },

  updateSchedule: async (MaLopHP, MaLich, data) => {
    const response = await apiClient.put(`/class-sections/${MaLopHP}/schedules/${MaLich}`, data);
    return response.data;
  },

  deleteSchedule: async (MaLopHP, MaLich) => {
    const response = await apiClient.delete(`/class-sections/${MaLopHP}/schedules/${MaLich}`);
    return response.data;
  },

  getEnrollments: async (MaLopHP) => {
    const response = await apiClient.get(`/class-sections/${MaLopHP}/enrollments`);
    return response.data;
  },
};
