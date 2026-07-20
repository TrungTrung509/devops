/**
 * Teacher Management API - CRUD for teachers
 * Backend prefix: /teachers
 *
 * Response wrapper (handled by apiClient interceptor):
 *   { status, success, message, data: ..., errorr }
 *   -> interceptor returns: { ...response, data: <unwrap data> }
 *
 * GET /teachers/  -> data = { items, total, skip, limit }
 * GET /teachers/{maGV} -> data = TeacherResponse
 * POST /teachers/ -> data = TeacherResponse
 * PUT /teachers/{maGV} -> data = TeacherResponse
 * PATCH /teachers/{maGV}/status -> data = TeacherResponse
 * DELETE /teachers/{maGV} -> data = null
 */

import apiClient from '@/services/apiClient';

// Standardized query key factory for React Query
export const teacherKeys = {
  all: ['admin', 'teachers'],
  list: (filters) => ['admin', 'teachers', 'list', filters],
  detail: (MaGV) => ['admin', 'teachers', 'detail', MaGV],
};

export const teacherApi = {
  /**
   * GET /teachers/
   * Query params (camelCase as backend expects):
   *   maCoSo, maKhoa, trangThai, keyword, skip, limit
   * Response: { items: Teacher[], total: int, skip, limit }
   */
  /**
   * GET /teachers/
   * Query params (camelCase as backend expects):
   *   maCoSo, maKhoa, trangThai, keyword, skip, limit
   * Response: { items: Teacher[], total: int, skip, limit }
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
    // Backend: skip is 0-based page index
    params.skip  = Math.max(Number(page) - 1, 0);
    params.limit = Number(pageSize);

    const response = await apiClient.get('/teachers/', { params });
    // apiClient unwraps wrapper: response.data = { items, total, skip, limit }
    return response.data;
  },

  /**
   * GET /teachers/{MaGV}
   * Response: TeacherResponse (PascalCase fields)
   */
  getById: async (MaGV) => {
    const response = await apiClient.get(`/teachers/${MaGV}`);
    return response.data;
  },

  /**
   * POST /teachers/
   * Body: TeacherCreate (PascalCase, Ho+Ten required, MaCoSo required)
   * email is lowercase in schema
   */
  create: async (data) => {
    // Backend TeacherCreate accepts: MaGV(optional), Ho, Ten, email(optional), SDT(optional),
    // NgaySinh, GioiTinh, DiaChi, HocVi, HocHam, MaCoSo(required), MaKhoa(optional),
    // TrangThai(optional), NgayVaoLam
    const payload = { ...data };
    // email field is lowercase in schema
    // Convert empty string for optional fields to undefined
    if (!payload.email) delete payload.email;
    if (!payload.MaGV || !payload.MaGV.trim()) delete payload.MaGV;

    const response = await apiClient.post('/teachers/', payload);
    return response.data;
  },

  /**
   * PUT /teachers/{MaGV}
   * Body: TeacherUpdate (includes MaCoSo for DB site routing)
   * TeacherUpdate: Ho, Ten, NgaySinh, GioiTinh, HocVi, HocHam, SDT,
   *               DiaChi, MaKhoa, TrangThai, NgayVaoLam, MaCoSo
   */
  update: async (MaGV, data) => {
    // TeacherUpdate includes MaCoSo (backend uses it for DB routing)
    const { MaGV: _m, ...updatePayload } = data;
    const response = await apiClient.put(`/teachers/${MaGV}`, updatePayload);
    return response.data;
  },

  /**
   * PATCH /teachers/{MaGV}/status
   * Body: { TrangThai }
   */
  updateStatus: async (MaGV, TrangThai) => {
    const response = await apiClient.patch(`/teachers/${MaGV}/status`, { TrangThai });
    return response.data;
  },

  /**
   * DELETE /teachers/{MaGV}
   */
  delete: async (MaGV) => {
    const response = await apiClient.delete(`/teachers/${MaGV}`);
    return response.data;
  },
};
