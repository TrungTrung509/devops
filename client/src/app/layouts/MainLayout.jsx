/**
 * MainLayout - Sidebar + Header + Content wrapper
 * Inspired by the screenshot: sidebar left, header top, content in middle
 */

import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Layout, Menu, Typography, Avatar, Dropdown, Space, Badge, Button } from 'antd';
import {
  HomeOutlined,
  BookOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
} from '@ant-design/icons';
import { useLogoutMutation } from '@/hooks/useAuth';
import { useCurrentUserQuery } from '@/hooks/useUser';
import { getUserDisplayName, getUserCode } from '@/utils/formatters';
import styles from './MainLayout.module.scss';

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  {
    key: '/dashboard',
    icon: <HomeOutlined />,
    label: 'Trang chủ',
  },
  {
    key: '/registration',
    icon: <BookOutlined />,
    label: 'Đăng ký môn học',
  },
];

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const { data: user, isLoading: userLoading } = useCurrentUserQuery();
  const logoutMutation = useLogoutMutation();

  const handleLogout = () => {
    logoutMutation.mutate();
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Thông tin cá nhân',
      disabled: true,
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
  const userCode = getUserCode(user);
  const roleLabel = user?.role === 'SinhVien' ? 'Sinh viên' : user?.role === 'GiangVien' ? 'Giảng viên' : user?.role || '';

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
                <BookOutlined style={{ fontSize: 20, color: '#fff' }} />
              </div>
              <div className={styles.logoText}>
                <span className={styles.logoTitle}>ĐKTC</span>
                <span className={styles.logoSubtitle}>PTIT</span>
              </div>
            </div>
          ) : (
            <div className={styles.logoCollapsed}>
              <div className={styles.logoIcon}>
                <BookOutlined style={{ fontSize: 18, color: '#fff' }} />
              </div>
            </div>
          )}
        </div>

        {/* Navigation Menu */}
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={['/dashboard']}
          items={menuItems}
          className={styles.menu}
        />

        {/* Collapse Toggle */}
        <div className={styles.collapseBtn}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            className={styles.collapseBtnInner}
          />
        </div>
      </Sider>

      <Layout>
        {/* Header */}
        <Header className={styles.header}>
          <div className={styles.headerLeft}>
            {/* Breadcrumb or page title area could go here */}
          </div>

          <div className={styles.headerRight}>
            {/* Notification bell */}
            <Badge count={0} size="small" offset={[-2, 2]}>
              <Button type="text" icon={<BellOutlined />} className={styles.iconBtn} />
            </Badge>

            {/* User dropdown */}
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={['click']}
            >
              <Space className={styles.userDropdown}>
                <Avatar
                  size={36}
                  style={{ backgroundColor: '#1677ff', flexShrink: 0 }}
                  icon={<UserOutlined />}
                />
                {!userLoading && user ? (
                  <div className={styles.userInfo}>
                    <Text className={styles.userName}>{displayName}</Text>
                    <Text className={styles.userRole}>{roleLabel} · {userCode}</Text>
                  </div>
                ) : (
                  <div className={styles.userInfo}>
                    <Text className={styles.userName}>Loading...</Text>
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
