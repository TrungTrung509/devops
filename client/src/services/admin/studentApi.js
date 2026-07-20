/**
 * Student Management API - CRUD for students
 * Backend prefix: /students
 *
 * Response wrapper (handled by apiClient interceptor):
 *   { status, success, message, data: ..., errorr }
 *   -> interceptor returns: { ...response, data: <unwrap data> }
 *
 * GET /students/    -> data = { items, total, skip, limit }
 * GET /students/{maSV} -> data = StudentResponse
 * POST /students/  -> data = StudentResponse
 * PUT /students/{maSV} -> data = StudentResponse
 * PATCH /students/{maSV}/status -> data = StudentResponse
 * DELETE /students/{maSV} -> data = null
 */

import apiClient from '@/services/apiClient';

// Standardized query key factory for React Query
export const studentKeys = {
  all: ['admin', 'students'],
  list: (filters) => ['admin', 'students', 'list', filters],
  detail: (MaSV) => ['admin', 'students', 'detail', MaSV],
};

export const studentApi = {
  /**
   * GET /students/
   * Query params (camelCase as backend expects):
   *   maCoSo, maKhoa, trangThai, keyword, skip, limit
   * Response: { items: Student[], total: int, skip, limit }
   */
  getAll: async (filters = {}) => {
    // Support both camelCase and PascalCase keys from component state
    const maCoSo    = filters.maCoSo    ?? filters.MaCoSo;
    const maKhoa    = filters.maKhoa    ?? filters.MaKhoa;
    const trangThai = filters.trangThai ?? filters.TrangThai;
    const keyword   = filters.keyword?.trim?.() || filters.keyword;
    const page      = filters.page ?? 1;
    const pageSize  = filters.pageSize ?? filters.limit ?? 10;

    const params = {};
    if (maCoSo)    params.maCoSo    = maCoSo;
    if (maKhoa)    params.maKhoa    = maKhoa;
    if (trangThai) params.trangThai = trangThai;
    if (keyword)   params.keyword   = keyword;
    // Backend: skip is 0-based page index (offset = skip * limit)
    params.skip  = Math.max(Number(page) - 1, 0);
    params.limit = Number(pageSize);

    const response = await apiClient.get('/students/', { params });
    // apiClient unwraps wrapper: response.data = { items, total, skip, limit }
    return response.data;
  },

  /**
   * GET /students/{MaSV}
   * Response: StudentResponse (PascalCase fields)
   */
  getById: async (MaSV) => {
    const response = await apiClient.get(`/students/${MaSV}`);
    return response.data;
  },

  /**
   * POST /students/
   * Body: StudentCreate (PascalCase, Ho+Ten required, MaCoSo required)
   * email is lowercase in schema
   */
  create: async (data) => {
    // Backend StudentCreate: MaSV(optional), Ho, Ten, email(optional), SDT(optional),
    // NgaySinh, GioiTinh, DiaChi, MaCoSo(required), MaKhoa(optional),
    // TrangThai(optional), NgayNhapHoc
    const payload = { ...data };
    // email field is lowercase in schema
    // Convert empty string for optional fields to undefined
    if (!payload.email) delete payload.email;
    if (!payload.MaSV || !payload.MaSV.trim()) delete payload.MaSV;

    const response = await apiClient.post('/students/', payload);
    return response.data;
  },

  /**
   * PUT /students/{MaSV}
   * Body: StudentUpdate (no MaCoSo, no email, no MaSV)
   * StudentUpdate: Ho, Ten, NgaySinh, GioiTinh, SDT, DiaChi, MaKhoa, TrangThai, NgayNhapHoc
   */
  update: async (MaSV, data) => {
    // Strip fields not in StudentUpdate schema
    const { MaSV: _m, MaCoSo: _c, email: _e, ...updatePayload } = data;
    const response = await apiClient.put(`/students/${MaSV}`, updatePayload);
    return response.data;
  },

  /**
   * PATCH /students/{MaSV}/status
   * Body: { TrangThai }
   */
  updateStatus: async (MaSV, TrangThai) => {
    const response = await apiClient.patch(`/students/${MaSV}/status`, { TrangThai });
    return response.data;
  },

  /**
   * DELETE /students/{MaSV}
   */
  delete: async (MaSV) => {
    const response = await apiClient.delete(`/students/${MaSV}`);
    return response.data;
  },
};
