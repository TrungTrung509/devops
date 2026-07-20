/**
 * Semester API
 */

import apiClient from './apiClient';

/**
 * GET /semesters/
 * Response: SemesterResponse[]
 * SemesterResponse: { maHocKy, namHoc, kySo, ngayBatDau, ngayKetThuc, trangThaiHocKy }
 */
export const semesterApi = {
  getAll: async () => {
    const response = await apiClient.get('/semesters/');
    return response.data;
  },

  getById: async (maHocKy) => {
    const response = await apiClient.get(`/semesters/${maHocKy}`);
    return response.data;
  },
};
