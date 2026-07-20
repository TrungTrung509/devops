/**
 * AdminLayout - Sidebar + Header + Content wrapper for admin area
 */

import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography, Avatar, Dropdown, Space, Badge, Button, Tag } from 'antd';
import {
  DashboardOutlined,
  BankOutlined,
  ApartmentOutlined,
  TeamOutlined,
  UserOutlined,
  BookOutlined,
  CalendarOutlined,
  ReadOutlined,
  HomeOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  ClusterOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useLogoutMutation } from '@/hooks/useAuth';
import { useCurrentUserQuery } from '@/hooks/useUser';
import { getUserDisplayName } from '@/utils/formatters';
import styles from './AdminLayout.module.scss';

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  {
    key: '/admin',
    icon: <DashboardOutlined />,
    label: 'Tổng quan',
  },
  {
    type: 'divider',
  },
  {
    key: 'manager-group',
    label: 'QUẢN LÝ',
    type: 'group',
  },
  {
    key: '/admin/branches',
    icon: <BankOutlined />,
    label: 'Cơ sở',
  },
  {
    key: '/admin/departments',
    icon: <ApartmentOutlined />,
    label: 'Khoa',
  },
  {
    key: '/admin/teachers',
    icon: <TeamOutlined />,
    label: 'Giảng viên',
  },
  {
    key: '/admin/students',
    icon: <UserOutlined />,
    label: 'Sinh viên',
  },
  {
    key: '/admin/courses',
    icon: <BookOutlined />,
    label: 'Học phần',
  },
  {
    key: '/admin/semesters',
    icon: <CalendarOutlined />,
    label: 'Học kỳ',
  },
  {
    key: '/admin/classrooms',
    icon: <HomeOutlined />,
    label: 'Phòng học',
  },
  {
    key: '/admin/class-sections',
    icon: <ReadOutlined />,
    label: 'Lớp học phần',
  },
  {
    type: 'divider',
  },
  {
    key: 'system-group',
    label: 'HỆ THỐNG',
    type: 'group',
  },
  {
    key: '/admin/failover',
    icon: <ClusterOutlined />,
    label: 'Failover',
  },
];

export default function AdminLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { data: user } = useCurrentUserQuery();
  const logoutMutation = useLogoutMutation();

  const handleMenuClick = ({ key }) => {
    if (key.startsWith('/admin')) {
      navigate(key);
    }
  };

  const selectedKey = menuItems.find(
    (item) => item.key === location.pathname
  )
    ? location.pathname
    : '/' + location.pathname.split('/').slice(1, 3).join('/');

  const handleLogout = () => {
    logoutMutation.mutate();
  };

  const userMenuItems = [
    {
      key: 'back-to-user',
      icon: <ExclamationCircleOutlined />,
      label: 'Quay lại trang Sinh viên',
      onClick: () => navigate('/dashboard'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Đăng xuất',
      danger: true,
      onClick: handleLogout,
    },
  ];

  const displayName = getUserDisplayName(user);

  return (
    <Layout className={styles.layout}>
      {/* Sidebar */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={240}
        collapsedWidth={80}
        className={styles.sider}
      >
        {/* Logo / Brand */}
        <div className={styles.logoArea}>
          {!collapsed ? (
            <div className={styles.logoExpanded}>
              <div className={styles.logoIcon}>
                <SettingOutlined style={{ fontSize: 18, color: '#fff' }} />
              </div>
              <div className={styles.logoText}>
                <span className={styles.logoTitle}>Admin Panel</span>
                <span className={styles.logoSubtitle}>PTIT</span>
              </div>
            </div>
          ) : (
            <div className={styles.logoCollapsed}>
              <div className={styles.logoIconSmall}>
                <SettingOutlined style={{ fontSize: 16, color: '#fff' }} />
              </div>
            </div>
          )}
        </div>

        {/* Navigation Menu */}
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={handleMenuClick}
          className={styles.menu}
        />

        {/* Collapse Toggle */}
        <div className={styles.collapseBtn}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            className={styles.collapseBtnInner}
          >
            {!collapsed && <span className={styles.collapseLabel}>Thu gọn</span>}
          </Button>
        </div>
      </Sider>

      <Layout>
        {/* Header */}
        <Header className={styles.header}>
          <div className={styles.headerLeft}>
            <Text className={styles.pageTitle}>
              {menuItems.find((item) => item.key === selectedKey)?.label || 'Admin'}
            </Text>
          </div>

          <div className={styles.headerRight}>
            {/* Admin badge */}
            <Tag color="red" className={styles.adminBadge}>Admin</Tag>

            {/* User dropdown */}
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={['click']}
            >
              <Space className={styles.userDropdown}>
                <Avatar
                  size={36}
                  style={{ backgroundColor: '#ff4d4f', flexShrink: 0 }}
                  icon={<SettingOutlined />}
                />
                {user ? (
                  <div className={styles.userInfo}>
                    <Text className={styles.userName}>{displayName}</Text>
                    <Text className={styles.userRole}>{user.username}</Text>
                  </div>
                ) : (
                  <div className={styles.userInfo}>
                    <Text className={styles.userName}>Admin</Text>
                  </div>
                )}
              </Space>
            </Dropdown>
          </div>
        </Header>

        {/* Main Content */}
        <Content className={`${styles.content} ${collapsed ? styles.contentCollapsed : ''}`}>
          <div className={styles.contentInner}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
