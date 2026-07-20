/**
 * DashboardPage - Home page with student summary
 */

import { Card, Row, Col, Statistic, Typography, Skeleton, Space, Button, Table, Tag, Empty } from 'antd';
import { BookOutlined, CheckCircleOutlined, ClockCircleOutlined, RightOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useCurrentUserQuery } from '@/hooks/useUser';
import { useEnrollmentHistoryQuery } from '@/hooks/useEnrollment';
import { getUserCode, formatDate, getEnrollmentStatusProps, buildFullName, getGenderLabel } from '@/utils/formatters';
import styles from './DashboardPage.module.scss';

const { Title, Text } = Typography;

export default function DashboardPage() {
  const { data: user, isLoading: userLoading } = useCurrentUserQuery();
  const { data: enrollments, isLoading: enrollLoading } = useEnrollmentHistoryQuery();

  const registeredCount = enrollments?.filter((e) => e.trangThaiDangKy === 'DaDangKy').length || 0;
  const totalCredits = enrollments
    ?.filter((e) => e.trangThaiDangKy === 'DaDangKy')
    .reduce((sum) => sum, 0);

  const recentEnrollments = enrollments?.slice(0, 5) || [];

  const historyColumns = [
    {
      title: 'Mã lớp',
      dataIndex: 'maLopHP',
      key: 'maLopHP',
      width: 120,
      render: (code) => <Text code style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: 'Tên môn học',
      dataIndex: 'tenHocPhan',
      key: 'tenHocPhan',
      ellipsis: true,
    },
    {
      title: 'Ngày đăng ký',
      dataIndex: 'ngayDangKy',
      key: 'ngayDangKy',
      width: 130,
      render: (date) => formatDate(date),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'trangThaiDangKy',
      key: 'trangThaiDangKy',
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
                  {buildFullName(user.ho, user.ten)?.charAt(0)?.toUpperCase() || 'S'}
                </span>
              </div>
              <div className={styles.welcomeText}>
                <Title level={3} className={styles.welcomeTitle}>
                  Xin chào, {buildFullName(user.ho, user.ten)}!
                </Title>
                <Text type="secondary" className={styles.welcomeSubtitle}>
                  Mã sinh viên: <strong>{user.maSV || getUserCode(user)}</strong>
                  {user.maCoSo && (
                    <> · Cơ sở: <strong>{user.maCoSo}</strong></>
                  )}
                </Text>
              </div>
            </>
          ) : null}
        </div>

        <Link to="/registration">
          <Button type="primary" size="large" icon={<BookOutlined />}>
            Đăng ký môn học
          </Button>
        </Link>
      </div>

      {/* Stats Row */}
      <Row gutter={[16, 16]} className={styles.statsRow}>
        <Col xs={24} sm={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="Môn học đã đăng ký"
              value={registeredCount}
              prefix={<BookOutlined style={{ color: '#1677ff' }} />}
              valueStyle={{ color: '#1677ff', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="Học phần đang theo học"
              value={registeredCount}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="Học phần đã hoàn thành"
              value={enrollments?.filter((e) => e.trangThaiDangKy === 'HoanThanh').length || 0}
              prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14', fontWeight: 600 }}
            />
          </Card>
        </Col>
      </Row>

      {/* Student Info Card */}
      {!userLoading && user && (
        <Card
          title="Thông tin sinh viên"
          className={styles.infoCard}
          extra={<Link to="/registration"><Button type="link">Chỉnh sửa</Button></Link>}
        >
          <Row gutter={[24, 16]}>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Họ và tên</Text>
                <Text className={styles.infoValue}>{buildFullName(user.ho, user.ten)}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Mã sinh viên</Text>
                <Text className={styles.infoValue}>{user.maSV || '—'}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Giới tính</Text>
                <Text className={styles.infoValue}>{getGenderLabel(user.gioiTinh) || '—'}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Ngày sinh</Text>
                <Text className={styles.infoValue}>{formatDate(user.ngaySinh) || '—'}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Số điện thoại</Text>
                <Text className={styles.infoValue}>{user.sdt || '—'}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Cơ sở</Text>
                <Text className={styles.infoValue}>{user.maCoSo || '—'}</Text>
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* Recent Enrollments */}
      <Card
        title="Đăng ký gần đây"
        className={styles.recentCard}
        extra={
          <Link to="/registration">
            <Button type="link" icon={<RightOutlined />}>
              Xem tất cả
            </Button>
          </Link>
        }
      >
        {enrollLoading ? (
          <Skeleton active paragraph={{ rows: 3 }} />
        ) : recentEnrollments.length > 0 ? (
          <Table
            dataSource={recentEnrollments}
            columns={historyColumns}
            rowKey="maDangKy"
            pagination={false}
            size="middle"
            className={styles.recentTable}
          />
        ) : (
          <Empty
            description="Chưa có đăng ký nào"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Link to="/registration">
              <Button type="primary" icon={<BookOutlined />}>
                Đăng ký ngay
              </Button>
            </Link>
          </Empty>
        )}
      </Card>
    </div>
  );
}
