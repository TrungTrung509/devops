/**
 * Classroom Query Keys - React Query key factory
 */
export const classroomKeys = {
  all: ['admin', 'classrooms'],
  list: (filters) => ['admin', 'classrooms', 'list', filters],
  detail: (MaPhong) => ['admin', 'classrooms', 'detail', MaPhong],
};

/**
 * Classroom API - CRUD for classrooms (Admin only for writes)
 * Backend returns: { status, success, message, data: { items: Classroom[], total: int } }
 * apiClient interceptor unwraps to: response.data = { items: [], total: ... }
 *
 * Filter query params supported:
 *   keyword - tìm theo mã phòng hoặc tên phòng (không phân biệt hoa thường)
 *   maCoSo  - lọc theo mã cơ sở (HADONG, NGOCTRUC, HOALAC)
 *   loaiPhong - lọc theo loại phòng (LyThuyet, ThucHanh, MayTinh, HoiTruong, etc.)
 *   trangThai - lọc theo trạng thái (HoatDong, NgungSuDung, BaoTri)
 */

import apiClient from '@/services/apiClient';

export const classroomApi = {
  getAll: async (filters = {}) => {
    const keyword    = filters.keyword?.trim?.() || undefined;
    const maCoSo     = filters.maCoSo     ?? filters.MaCoSo     ?? undefined;
    const loaiPhong  = filters.loaiPhong  ?? filters.LoaiPhong  ?? undefined;
    const trangThai  = filters.trangThai  ?? filters.TrangThai  ?? undefined;

    const params = {};
    if (keyword)    params.keyword    = keyword;
    if (maCoSo)     params.maCoSo     = maCoSo;
    if (loaiPhong)  params.loaiPhong  = loaiPhong;
    if (trangThai)  params.trangThai  = trangThai;

    const response = await apiClient.get('/classrooms/', { params });
    // Response is already unwrapped by apiClient interceptor: { items: [], total: ... }
    return response.data;
  },

  getById: async (MaPhong) => {
    const response = await apiClient.get(`/classrooms/${MaPhong}`);
    return response.data;
  },

  create: async (data) => {
    const response = await apiClient.post('/classrooms/', data);
    return response.data;
  },

  update: async (MaPhong, data) => {
    const response = await apiClient.put(`/classrooms/${MaPhong}`, data);
    return response.data;
  },

  delete: async (MaPhong) => {
    const response = await apiClient.delete(`/classrooms/${MaPhong}`);
    return response.data;
  },
};
