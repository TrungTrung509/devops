/**
 * Class Section (LopHocPhan) API
 */

import apiClient from './apiClient';

/**
 * GET /class-sections/
 * Query params: maCoSo, maHocKy, maKhoa, trangThai, keyword, skip, limit
 * Response: CourseSectionListResponse[]
 * CourseSectionListResponse: {
 *   maLopHP, maHocPhan, tenHocPhan, maHocKy, maCoSo, maGV,
 *   tenLopHP, siSoToiDa, siSoHienTai, soChoConLai,
 *   hinhThucHoc, trangThaiLop, soLuongLichHoc, ngayTao
 * }
 */
export const classSectionApi = {
  getAll: async (params = {}) => {
    const response = await apiClient.get('/class-sections/', { params });
    return response.data;
  },

  getById: async (maLopHP) => {
    const response = await apiClient.get(`/class-sections/${maLopHP}`);
    return response.data;
  },
};
