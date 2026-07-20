/**
 * Auth Utilities
 * Centralizes role constants, normalization, and JWT decoding.
 *
 * Backend roles: "Admin", "SinhVien", "GiangVien" (PascalCase)
 * We normalize to PascalCase for internal use: "Admin", "SinhVien", "GiangVien"
 */

import { tokenStorage } from '@/services/authApi';

export const ROLES = {
  ADMIN: 'Admin',
  SINH_VIEN: 'SinhVien',
  GIANG_VIEN: 'GiangVien',
};

/**
 * Normalize role from JWT token (uppercase) to PascalCase for internal use.
 */
export function normalizeRole(role) {
  if (!role) return null;
  const upper = role.toUpperCase();
  if (upper === 'ADMIN') return ROLES.ADMIN;
  if (upper === 'SINHVIEN') return ROLES.SINH_VIEN;
  if (upper === 'GIANGVIEN') return ROLES.GIANG_VIEN;
  return role; // fallback as-is
}

/**
 * Get role directly from JWT token (sync, no API call).
 * Returns normalized role string or null if no token.
 */
export function getUserRole() {
  try {
    const token = tokenStorage.getAccessToken();
    if (!token) return null;
    // JWT payload is the middle part (base64url encoded)
    const payload = JSON.parse(atob(token.split('.')[1]));
    return normalizeRole(payload.role);
  } catch {
    return null;
  }
}

/**
 * Decode JWT token to get full payload.
 * Returns null if token invalid/missing.
 */
export function decodeToken() {
  try {
    const token = tokenStorage.getAccessToken();
    if (!token) return null;
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
}

/**
 * Redirect destination based on normalized role.
 */
export function getRedirectPath(role) {
  if (role === ROLES.ADMIN) return '/admin/dashboard';
  if (role === ROLES.SINH_VIEN) return '/student';
  if (role === ROLES.GIANG_VIEN) return '/teacher';
  return '/dashboard';
}
