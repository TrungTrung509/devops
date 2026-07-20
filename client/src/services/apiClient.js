/**
 * API Client - Centralized axios instance for all API calls
 * Handles base URL, auth headers, response normalization, and error handling
 */

import axios from 'axios';

const BASE_URL = 'http://localhost:8000/';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});


// Request Interceptor: Attach auth token

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);


// Response Interceptor: Normalize API response shape
// Standard wrapper: { status, success, message, data, errorr }
// Login endpoint: { access_token, refresh_token, token_type } (no wrapper)

apiClient.interceptors.response.use(
  (response) => {
    const payload = response.data;

    // If payload has 'success' field -> standard wrapper format
    if (payload && typeof payload === 'object' && 'success' in payload) {
      if (payload.success === false || payload.status >= 400) {
        // Extract the most descriptive message available
        const errorMsg =
          payload.message ||
          (payload.errorr?.details ? String(payload.errorr.details) : null) ||
          (Array.isArray(payload.errorr)
            ? payload.errorr.map((e) => e.msg || e.message || JSON.stringify(e)).join('; ')
            : null) ||
          'An error occurred';
        const apiError = new Error(errorMsg);
        apiError.isApiError = true;
        apiError.status = payload.status;
        apiError.data = payload.data;
        apiError.details = payload.errorr;
        apiError.backendMessage = payload.message || errorMsg;
        return Promise.reject(apiError);
      }
      // Success with wrapper -> unwrap data field
      return { ...response, data: payload.data, _meta: payload };
    }

    // Raw response (e.g., login token, or direct object without wrapper)
    return response;
  },
  (error) => {
    if (error.config && error.config._retry) {
      return Promise.reject(error);
    }

    if (error.response) {
      const { status, data } = error.response;

      if (status === 401) {
        const err = new Error(data?.message || 'Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.');
        err.isApiError = true;
        err.isAuthError = true;
        err.status = 401;
        err.data = data;
        return Promise.reject(err);
      }

      if (status === 403) {
        const err = new Error(data?.message || 'Bạn không có quyền thực hiện thao tác này.');
        err.isApiError = true;
        err.status = 403;
        err.data = data;
        return Promise.reject(err);
      }

      if (status === 422) {
        const messages = data?.errorr?.map ? data.errorr.map((e) => e.msg).join(', ') : data?.message || 'Dữ liệu không hợp lệ';
        const err = new Error(messages);
        err.isApiError = true;
        err.status = 422;
        err.data = data;
        return Promise.reject(err);
      }

      if (status >= 500) {
        const err = new Error(data?.message || 'Lỗi server. Vui lòng thử lại sau.');
        err.isApiError = true;
        err.status = status;
        err.data = data;
        return Promise.reject(err);
      }
    }

    // Network error (no response at all)
    if (!error.response) {
      const err = new Error('Không thể kết nối server. Vui lòng kiểm tra kết nối mạng.');
      err.isApiError = true;
      err.status = 0;
      return Promise.reject(err);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
