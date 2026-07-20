/**
 * StudentLayout - Sidebar + Header + Content for SinhVien
 * Modern Ant Design layout with dark sidebar
 */

import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography, Avatar, Dropdown, Space, Badge, Button, Tag } from 'antd';
import {
  HomeOutlined,
  BookOutlined,
  HistoryOutlined,
  CalendarOutlined,
  UserOutlined,
  LockOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  SwapOutlined,
} from '@ant-design/icons';
import { useLogoutMutation } from '@/hooks/useAuth';
import { useCurrentUserQuery } from '@/hooks/useUser';
import { getUserDisplayName, getUserCode, buildFullName } from '@/utils/formatters';
import styles from './StudentLayout.module.scss';

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  {
    key: '/student',
    icon: <HomeOutlined />,
    label: 'Trang chủ',
  },
  {
    key: '/student/class-sections',
    icon: <BookOutlined />,
    label: 'Lớp học phần',
  },
  {
    key: '/student/enrollments',
    icon: <SwapOutlined />,
    label: 'Đăng ký của tôi',
  },
  {
    key: '/student/schedule',
    icon: <CalendarOutlined />,
    label: 'Lịch học',
  },
];

function getSelectedKey(pathname) {
  if (pathname === '/student' || pathname === '/student/') return '/student';
  const match = menuItems.find((item) => pathname.startsWith(item.key) && item.key !== '/student');
  return match ? match.key : '/student';
}

export default function StudentLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { data: user, isLoading: userLoading } = useCurrentUserQuery();
  const logoutMutation = useLogoutMutation();

  const selectedKey = getSelectedKey(location.pathname);

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logoutMutation.mutate();
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Thông tin cá nhân',
      onClick: () => navigate('/student/profile'),
    },
    {
      key: 'change-password',
      icon: <LockOutlined />,
      label: 'Đổi mật khẩu',
      onClick: () => navigate('/student/profile?action=change-password'),
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
  const userCode = user?.maSV || getUserCode(user);
  const roleLabel = 'Sinh viên';

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
        {/* Logo */}
        <div className={styles.logoArea}>
          {!collapsed ? (
            <div className={styles.logoExpanded}>
              <div className={styles.logoIcon}>
                <BookOutlined style={{ fontSize: 20, color: '#fff' }} />
              </div>
              <div className={styles.logoText}>
                <span className={styles.logoTitle}>PTIT</span>
                <span className={styles.logoSubtitle}>Sinh viên</span>
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
          selectedKeys={[selectedKey]}
          items={menuItems}
          className={styles.menu}
          onClick={handleMenuClick}
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
            <Text className={styles.pageTitle}>
              {menuItems.find((m) => m.key === selectedKey)?.label || 'Trang chủ'}
            </Text>
          </div>

          <div className={styles.headerRight}>
            <Badge count={0} size="small" offset={[-2, 2]}>
              <Button type="text" icon={<BellOutlined />} className={styles.iconBtn} />
            </Badge>

            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={['click']}
            >
              <Space className={styles.userDropdown}>
                <Avatar
                  size={36}
                  style={{ backgroundColor: '#52c41a', flexShrink: 0 }}
                  icon={<UserOutlined />}
                />
                {!userLoading && user ? (
                  <div className={styles.userInfo}>
                    <Text className={styles.userName}>{displayName}</Text>
                    <div className={styles.userMeta}>
                      <Tag color="green" style={{ fontSize: 11, lineHeight: '16px', padding: '0 4px' }}>
                        {roleLabel}
                      </Tag>
                      <Text className={styles.userCode}>{userCode}</Text>
                    </div>
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
