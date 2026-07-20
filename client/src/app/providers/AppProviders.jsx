/**
 * AppProviders - Wraps the application with React Query, Ant Design, and Auth providers
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import viVN from 'antd/locale/vi_VN';
import queryClient from '@/services/queryClient';
import { AuthProvider } from './AuthContext';

const theme = {
  token: {
    colorPrimary: '#1677ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1677ff',
    borderRadius: 8,
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize: 14,
    colorBgContainer: '#ffffff',
    colorBgLayout: '#f0f2f5',
  },
  components: {
    Layout: {
      headerBg: '#ffffff',
      bodyBg: '#f0f2f5',
      siderBg: '#001529',
    },
    Menu: {
      darkItemBg: 'transparent',
      darkItemColor: 'rgba(255, 255, 255, 0.65)',
      darkItemHoverBg: 'rgba(255, 255, 255, 0.08)',
      darkItemSelectedBg: 'rgba(255, 255, 255, 0.15)',
      darkItemSelectedColor: '#ffffff',
    },
    Table: {
      headerBg: '#fafafa',
      headerColor: '#666666',
      rowHoverBg: '#fafafa',
    },
    Button: {
      primaryShadow: '0 2px 4px rgba(22, 119, 255, 0.2)',
    },
    Card: {
      borderRadiusLG: 12,
    },
  },
};

export default function AppProviders({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={theme} locale={viVN}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </ConfigProvider>
    </QueryClientProvider>
  );
}
