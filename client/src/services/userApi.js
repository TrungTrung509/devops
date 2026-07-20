/**
 * User API - Current user profile
 */

import apiClient from './apiClient';

/**
 * GET /users/me
 * Response: StudentResponse | TeacherResponse | UserResponse
 * StudentResponse: {
 *   userId, username, email, role, MaCoSo, status, NgayTao,
 *   ho, ten, ngaySinh, gioiTinh, sdt, diaChi,
 *   maSV, maKhoa, trangThai, ngayNhapHoc
 * }
 */
export const userApi = {
  getCurrentUser: async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },

  changePassword: async ({ oldPassword, newPassword, confirmPassword }) => {
    const response = await apiClient.put('/users/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
    return response.data;
  },
};
