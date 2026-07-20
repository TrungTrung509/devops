/**
 * Failover API - System failover/replication management (Admin only)
 */

import apiClient from '@/services/apiClient';

export const failoverApi = {
  getStatus: async () => {
    const response = await apiClient.get('/failover/status');
    return response.data;
  },

  manualFailover: async (targetSite) => {
    const response = await apiClient.post('/failover/manual', { target_site: targetSite });
    return response.data;
  },

  triggerAutoFailover: async () => {
    const response = await apiClient.post('/failover/auto');
    return response.data;
  },

  configureAutoFailover: async (enabled) => {
    const response = await apiClient.post('/failover/config/auto', { enabled });
    return response.data;
  },
};
