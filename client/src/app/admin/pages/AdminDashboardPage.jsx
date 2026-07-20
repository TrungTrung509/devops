/**
 * Admin Dashboard Page - Overview of all modules
 */

import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Skeleton, Button, Table, Tag } from 'antd';
import {
  BankOutlined,
  TeamOutlined,
  BookOutlined,
  CalendarOutlined,
  HomeOutlined,
  ReadOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { branchApi } from '@/services/admin/branchApi';
import { studentApi } from '@/services/admin/studentApi';
import { teacherApi } from '@/services/admin/teacherApi';
import { courseApi } from '@/services/admin/courseApi';
import { semesterApi } from '@/services/admin/semesterApi';
import { classroomApi } from '@/services/admin/classroomApi';
import { classSectionApi } from '@/services/admin/classSectionApi';
import { useCurrentUserQuery } from '@/hooks/useUser';
import { getUserDisplayName } from '@/utils/formatters';
import styles from './AdminDashboard.module.scss';

const { Title, Text } = Typography;

const moduleCards = [
  { key: 'branches', title: 'Cơ sở', icon: <BankOutlined />, path: '/admin/branches', color: '#1677ff' },
  { key: 'departments', title: 'Khoa', icon: <BankOutlined />, path: '/admin/departments', color: '#722ed1', disabled: true },
  { key: 'teachers', title: 'Giảng viên', icon: <TeamOutlined />, path: '/admin/teachers', color: '#13c2c2' },
  { key: 'students', title: 'Sinh viên', icon: <TeamOutlined />, path: '/admin/students', color: '#52c2c2' },
  { key: 'courses', title: 'Học phần', icon: <BookOutlined />, path: '/admin/courses', color: '#fa8c16' },
  { key: 'semesters', title: 'Học kỳ', icon: <CalendarOutlined />, path: '/admin/semesters', color: '#faad14' },
  { key: 'classrooms', title: 'Phòng học', icon: <HomeOutlined />, path: '/admin/classrooms', color: '#eb2f96' },
  { key: 'class-sections', title: 'Lớp học phần', icon: <ReadOutlined />, path: '/admin/class-sections', color: '#fa541c' },
];

// Helper to extract array from paginated response
function extractItems(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  return data.items || [];
}

export default function AdminDashboardPage() {
  const { data: user, isLoading: userLoading } = useCurrentUserQuery();
  const [stats, setStats] = useState({
    branches: 0,
    teachers: 0,
    students: 0,
    courses: 0,
    semesters: 0,
    classrooms: 0,
    classSections: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentSections, setRecentSections] = useState([]);

  useEffect(() => {
    Promise.allSettled([
      branchApi.getAll(),
      teacherApi.getAll(),
      studentApi.getAll(),
      courseApi.getAll(),
      semesterApi.getAll(),
      classroomApi.getAll(),
      classSectionApi.getAll(),
    ]).then((results) => {
      const [branches, teachers, students, courses, semesters, classrooms, classSections] = results.map((r) => extractItems(r.value));

      setStats({
        branches: branches.length,
        teachers: teachers.length,
        students: students.length,
        courses: courses.length,
        semesters: semesters.length,
        classrooms: classrooms.length,
        classSections: classSections.length,
      });
      setRecentSections(classSections.slice(0, 5));
      setLoading(false);
    });
  }, []);

  const getStatusProps = (status) => {
    const map = { Mo: { color: 'success', label: 'Mở' }, Dong: { color: 'warning', label: 'Đóng' }, Huy: { color: 'error', label: 'Hủy' } };
    return map[status] || { color: 'default', label: status || '—' };
  };

  const recentColumns = [
    {
      title: 'Mã LHP',
      dataIndex: 'MaLopHP',
      key: 'MaLopHP',
      width: 130,
      render: (code) => <Text code style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: 'Tên học phần',
      dataIndex: 'TenHocPhan',
      key: 'TenHocPhan',
      ellipsis: true,
    },
    {
      title: 'Cơ sở',
      dataIndex: 'MaCoSo',
      key: 'MaCoSo',
      width: 120,
      render: (v) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: 'Sĩ số',
      key: 'siSo',
      width: 100,
      render: (_, record) => `${record.SiSoHienTai ?? 0}/${record.SiSoToiDa ?? 0}`,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThaiLop',
      key: 'TrangThaiLop',
      width: 90,
      render: (status) => {
        const p = getStatusProps(status);
        return <Tag color={p.color}>{p.label}</Tag>;
      },
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.welcomeSection}>
        <div className={styles.welcomeContent}>
          {userLoading ? (
            <Skeleton.Avatar size={64} active />
          ) : (
            <>
              <div className={styles.welcomeIcon}>
                <BankOutlined style={{ fontSize: 28, color: '#fff' }} />
              </div>
              <div>
                <Title level={3} className={styles.welcomeTitle}>
                  Xin chào, {getUserDisplayName(user)}!
                </Title>
                <Text className={styles.welcomeSubtitle}>
                  Quản trị viên hệ thống · Truy cập tất cả module quản lý
                </Text>
              </div>
            </>
          )}
        </div>
      </div>

      <Row gutter={[16, 16]} className={styles.statsRow}>
        {[
          { title: 'Cơ sở', value: stats.branches, icon: <BankOutlined />, color: '#1677ff' },
          { title: 'Giảng viên', value: stats.teachers, icon: <TeamOutlined />, color: '#13c2c2' },
          { title: 'Sinh viên', value: stats.students, icon: <TeamOutlined />, color: '#52c2c2' },
          { title: 'Học phần', value: stats.courses, icon: <BookOutlined />, color: '#fa8c16' },
          { title: 'Học kỳ', value: stats.semesters, icon: <CalendarOutlined />, color: '#faad14' },
          { title: 'Phòng học', value: stats.classrooms, icon: <HomeOutlined />, color: '#eb2f96' },
          { title: 'Lớp HP', value: stats.classSections, icon: <ReadOutlined />, color: '#fa541c' },
        ].map((stat) => (
          <Col xs={12} sm={8} md={6} lg={3} key={stat.title}>
            {loading ? (
              <Card className={styles.statCard}><Skeleton active paragraph={{ rows: 1 }} /></Card>
            ) : (
              <Card className={styles.statCard}>
                <Statistic
                  title={stat.title}
                  value={stat.value}
                  prefix={<span style={{ color: stat.color }}>{stat.icon}</span>}
                  valueStyle={{ color: stat.color, fontWeight: 700 }}
                />
              </Card>
            )}
          </Col>
        ))}
      </Row>

      <Card title="Truy cập nhanh" className={styles.moduleCard}>
        <Row gutter={[12, 12]}>
          {moduleCards.map((mod) => (
            <Col xs={12} sm={8} md={6} lg={3} key={mod.key}>
              <Link to={mod.path}>
                <Card className={styles.moduleItem} hoverable={!mod.disabled}>
                  <div className={styles.moduleIcon} style={{ background: mod.color + '18', color: mod.color }}>
                    {mod.icon}
                  </div>
                  <Text className={styles.moduleName}>{mod.title}</Text>
                  {mod.disabled && <Tag color="default" style={{ marginTop: 4 }}>Sắp ra mắt</Tag>}
                </Card>
              </Link>
            </Col>
          ))}
        </Row>
      </Card>

      <Card
        title="Lớp học phần gần đây"
        extra={<Link to="/admin/class-sections"><Button type="link" size="small">Xem tất cả</Button></Link>}
        className={styles.recentCard}
      >
        {loading ? (
          <Skeleton active paragraph={{ rows: 3 }} />
        ) : recentSections.length > 0 ? (
          <Table
            dataSource={recentSections}
            columns={recentColumns}
            rowKey="MaLopHP"
            pagination={false}
            size="middle"
          />
        ) : (
          <Text type="secondary">Chưa có lớp học phần nào</Text>
        )}
      </Card>
    </div>
  );
}
