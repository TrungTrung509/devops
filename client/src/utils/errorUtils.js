/**
 * API Error Message Extraction Utility
 *
 * Extracts a human-readable error message from backend error responses.
 * Backend standard error format:
 *   { status, success, false, message, data, errorr }
 *   { status, success, false, message, data, errorr: { code, details, field } }
 *   { detail: "string message" }
 *   { message: "string message" }
 *   FastAPI validation: { detail: [{ loc, msg, type }] }
 *
 * Usage:
 *   import { getApiErrorMessage } from '@/utils/errorUtils';
 *   message.error(getApiErrorMessage(error, 'Đã xảy ra lỗi'));
 */

/**
 * Extract the best available error message from an error object.
 *
 * Priority order:
 *  1. error.backendMessage    — set by apiClient interceptor when response has API wrapper
 *  2. error.message          — could be from axios, or set by interceptor
 *  3. error.response?.data?.message  — raw axios response
 *  4. error.response?.data?.detail   — FastAPI direct detail
 *  5. FastAPI validation array: format each { loc, msg } as "field: msg"
 *  6. error.details           — from payload.errorr.details
 *  7. fallback               — generic Vietnamese fallback
 *
 * @param {unknown} error - Any error object (from axios, mutation, etc.)
 * @param {string} [fallback] - Fallback message if nothing extracted
 * @returns {string} The extracted error message
 */
export function getApiErrorMessage(error, fallback = 'Đã xảy ra lỗi. Vui lòng thử lại.') {
  if (!error) return fallback;

  // 1. backendMessage set by apiClient interceptor (most reliable)
  if (error.backendMessage) return error.backendMessage;

  // 2. Direct message set by interceptor or custom error
  if (error.message && typeof error.message === 'string') {
    // Avoid returning raw axios/generic messages that are unhelpful
    const rawAxiosMessages = [
      'Request failed with status code',
      'Network Error',
      'timeout of',
      'ECONNREFUSED',
      'ERR_',
    ];
    const isRawAxios = rawAxiosMessages.some((m) => error.message.includes(m));
    if (!isRawAxios) return error.message;
  }

  // 3. Axios response — try response.data.message first
  if (error.response?.data) {
    const data = error.response.data;

    // Try .message (backend API wrapper or direct)
    if (data.message && typeof data.message === 'string' && data.message.trim()) {
      return data.message;
    }

    // Try .detail (FastAPI default or HTTPException detail)
    if (data.detail && typeof data.detail === 'string' && data.detail.trim()) {
      return data.detail;
    }

    // FastAPI validation error array: [{ loc, msg, type }]
    if (Array.isArray(data.detail)) {
      const formatted = data.detail
        .filter((e) => e && typeof e === 'object' && e.msg)
        .map((e) => {
          const loc = Array.isArray(e.loc) ? e.loc.slice(1).join('.') : '';
          return loc ? `${loc}: ${e.msg}` : e.msg;
        })
        .filter(Boolean);

      if (formatted.length > 0) {
        return formatted.join('; ');
      }
    }

    // Try nested payload format (rare, edge case)
    if (typeof data === 'object') {
      if (data.payload?.message) return data.payload.message;
      if (data.payload?.error) return data.payload.error;
    }
  }

  // 4. From interceptor: error.details (payload.errorr.details)
  if (error.details && typeof error.details === 'string' && error.details.trim()) {
    return error.details;
  }

  // 5. Status-based generic messages (only if we know the status)
  if (error.status === 401) {
    return 'Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.';
  }
  if (error.status === 403) {
    return 'Bạn không có quyền thực hiện thao tác này.';
  }
  if (error.status === 0) {
    return 'Không thể kết nối server. Vui lòng kiểm tra kết nối mạng.';
  }

  return fallback;
}

/**
 * Check if an error is an API error (set by the apiClient interceptor).
 */
export function isApiError(error) {
  return error && error.isApiError === true;
}

/**
 * Check if an error is an authentication error (401).
 */
export function isAuthError(error) {
  return error && error.isAuthError === true;
}

/**
 * Get the HTTP status code from an error.
 */
export function getErrorStatus(error) {
  if (!error) return null;
  if (typeof error.status === 'number') return error.status;
  if (error.response?.status) return error.response.status;
  return null;
}
