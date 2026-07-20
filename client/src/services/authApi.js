/**
 * Auth API - Login, logout, refresh token
 */

import apiClient from './apiClient';

/**
 * POST /auth/login
 * Raw response (no wrapper): { access_token, refresh_token, token_type }
 */
export const authApi = {
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await apiClient.post('/auth/login', formData.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    // Login returns raw object { access_token, ... } — no wrapper
    return response.data;
  },

  /**
   * POST /auth/refresh
   * Raw response: { access_token, refresh_token, token_type }
   */
  refreshToken: async (refreshToken) => {
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  /**
   * POST /auth/logout
   */
  logout: async (refreshToken) => {
    await apiClient.post('/auth/logout', { refresh_token: refreshToken });
  },
};

/**
 * Token storage helpers
 */
export const tokenStorage = {
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),

  setTokens: ({ access_token, refresh_token }) => {
    if (access_token) localStorage.setItem('access_token', access_token);
    if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
  },

  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  isAuthenticated: () => !!localStorage.getItem('access_token'),
};
