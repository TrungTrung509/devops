/**
 * Student Dashboard - Home page for SinhVien
 */

import { Card, Row, Col, Statistic, Typography, Skeleton, Button, Table, Tag, Empty, Space } from 'antd';
import {
  BookOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  UserOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { studentApi, studentEnrollmentApi, studentClassSectionApi } from '@/services/studentApi';
import {
  buildFullName,
  getGenderLabel,
  getStudentStatusProps,
  getBranchLabel,
  getEnrollmentStatusProps,
  formatDate,
} from '@/utils/formatters';
import styles from './StudentPage.module.scss';

const { Title, Text } = Typography;

export default function StudentDashboardPage() {
  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ['student', 'profile'],
    queryFn: studentApi.getProfile,
    staleTime: 5 * 60 * 1000,
  });

  const { data: enrollmentsResp, isLoading: enrollLoading } = useQuery({
    queryKey: ['student', 'enrollments'],
    queryFn: () => studentEnrollmentApi.getHistory(),
    staleTime: 2 * 60 * 1000,
  });

  const enrollments = Array.isArray(enrollmentsResp) ? enrollmentsResp : [];

  const registeredCount = enrollments.filter((e) => e.TrangThaiDangKy === 'DaDangKy').length;
  const completedCount = enrollments.filter((e) => e.TrangThaiDangKy === 'HoanThanh').length;
  const recentEnrollments = enrollments.slice(0, 5);

  const historyColumns = [
    {
      title: 'Mã lớp',
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
      title: 'Học kỳ',
      dataIndex: 'MaHocKy',
      key: 'MaHocKy',
      width: 100,
    },
    {
      title: 'Ngày đăng ký',
      dataIndex: 'NgayDangKy',
      key: 'NgayDangKy',
      width: 140,
      render: (date) => formatDate(date),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThaiDangKy',
      key: 'TrangThaiDangKy',
      width: 130,
      render: (status) => {
        const props = getEnrollmentStatusProps(status);
        return <Tag color={props.color}>{props.label}</Tag>;
      },
    },
  ];

  return (
    <div className={styles.page}>
      {/* Welcome Header */}
      <div className={styles.welcomeSection}>
        <div className={styles.welcomeContent}>
          {userLoading ? (
            <>
              <Skeleton.Avatar size={64} active />
              <div className={styles.welcomeText}>
                <Skeleton.Input active style={{ width: 200, height: 28 }} />
                <Skeleton.Input active style={{ width: 150, height: 18 }} />
              </div>
            </>
          ) : user ? (
            <>
              <div className={styles.welcomeAvatar}>
                <span className={styles.avatarInitial}>
                  {buildFullName(user.Ho, user.Ten)?.charAt(0)?.toUpperCase() || 'S'}
                </span>
              </div>
              <div className={styles.welcomeText}>
                <Title level={3} className={styles.welcomeTitle}>
                  Xin chào, {buildFullName(user.Ho, user.Ten)}!
                </Title>
                <Text type="secondary" className={styles.welcomeSubtitle}>
                  Mã sinh viên: <strong>{user.MaSV || user.UserId || user.userId}</strong>
                  {user.MaCoSo && <> · {getBranchLabel(user.MaCoSo)}</>}
                </Text>
              </div>
            </>
          ) : null}
        </div>

        <Space>
          <Link to="/student/class-sections">
            <Button type="primary" size="large" icon={<BookOutlined />}>
              Đăng ký học phần
            </Button>
          </Link>
        </Space>
      </div>

      {/* Stats Row */}
      <Row gutter={[16, 16]} className={styles.statsRow}>
        <Col xs={24} sm={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="Lớp đã đăng ký"
              value={registeredCount}
              prefix={<BookOutlined style={{ color: '#1677ff' }} />}
              valueStyle={{ color: '#1677ff', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="Lớp đang theo học"
              value={registeredCount}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="Lớp đã hoàn thành"
              value={completedCount}
              prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14', fontWeight: 600 }}
            />
          </Card>
        </Col>
      </Row>

      {/* Student Info Card */}
      {!userLoading && user && (
        <Card
          title={
            <Space>
              <UserOutlined style={{ color: '#1677ff' }} />
              Thông tin sinh viên
            </Space>
          }
          className={styles.infoCard}
          extra={
            <Link to="/student/profile">
              <Button type="link" icon={<RightOutlined />}>Chi tiết</Button>
            </Link>
          }
        >
          <Row gutter={[24, 16]}>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Họ và tên</Text>
                <Text className={styles.infoValue}>{buildFullName(user.Ho, user.Ten)}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Mã sinh viên</Text>
                <Text className={styles.infoValue}>{user.MaSV || '—'}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Giới tính</Text>
                <Text className={styles.infoValue}>{getGenderLabel(user.GioiTinh)}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Ngày sinh</Text>
                <Text className={styles.infoValue}>{formatDate(user.NgaySinh)}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Cơ sở</Text>
                <Text className={styles.infoValue}>{getBranchLabel(user.MaCoSo)}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Trạng thái</Text>
                {(() => {
                  const sp = getStudentStatusProps(user.TrangThai);
                  return <Tag color={sp.color}>{sp.label}</Tag>;
                })()}
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* Recent Enrollments */}
      <Card
        title={
          <Space>
            <ClockCircleOutlined style={{ color: '#1677ff' }} />
            Đăng ký gần đây
          </Space>
        }
        className={styles.recentCard}
        extra={
          <Link to="/student/enrollments">
            <Button type="link" icon={<RightOutlined />}>Xem tất cả</Button>
          </Link>
        }
      >
        {enrollLoading ? (
          <Skeleton active paragraph={{ rows: 3 }} />
        ) : recentEnrollments.length > 0 ? (
          <Table
            dataSource={recentEnrollments}
            columns={historyColumns}
            rowKey="MaDangKy"
            pagination={false}
            size="middle"
            className={styles.recentTable}
          />
        ) : (
          <Empty
            description="Chưa có đăng ký nào"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Link to="/student/class-sections">
              <Button type="primary" icon={<BookOutlined />}>Đăng ký ngay</Button>
            </Link>
          </Empty>
        )}
      </Card>
    </div>
  );
}
