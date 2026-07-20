/**
 * Enrollment API - Register, cancel, history
 */

import apiClient from './apiClient';

/**
 * POST /enrollments/register
 * Body: { maLopHP, ghiChu? }
 * Response: RegistrationResult
 * RegistrationResult: {
 *   maLopHP, status ('Success'|'Failed'), message,
 *   enrollment_id, action ('REGISTER'|'SWITCH'), old_ma_lop_hp
 * }
 */
export const enrollmentApi = {
  register: async ({ maLopHP }) => {
    const response = await apiClient.post('/enrollments/register', {
      MaLopHP: maLopHP,
    });
    return response.data;
  },

  /**
   * GET /enrollments/history
   * Query params: maHocKy?
   * Response: EnrollmentHistoryResponse[]
   * EnrollmentHistoryResponse: {
   *   maDangKy, maSV, maLopHP, tenLopHP, tenHocPhan, maHocKy,
   *   ngayDangKy, trangThaiDangKy ('DaDangKy'|'HoanThanh'|'DaHuy'), maCoSo
   * }
   */
  getHistory: async (params = {}) => {
    const response = await apiClient.get('/enrollments/history', { params });
    return response.data;
  },

  /**
   * DELETE /enrollments/cancel
   * Query params: maLopHP
   */
  cancel: async (maLopHP) => {
    const response = await apiClient.delete('/enrollments/cancel', {
      params: { maLopHP },
    });
    return response.data;
  },
};
