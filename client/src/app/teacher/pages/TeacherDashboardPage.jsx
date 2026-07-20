/**
 * Teacher Dashboard - Home page for GiangVien
 */

import { Card, Row, Col, Statistic, Typography, Skeleton, Button, Table, Tag, Empty, Space } from 'antd';
import {
  BookOutlined,
  TeamOutlined,
  UserOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { teacherApi, teacherClassSectionApi } from '@/services/teacherApi';
import {
  buildFullName,
  getGenderLabel,
  getTeacherStatusProps,
  getBranchLabel,
  getClassSectionStatusProps,
  formatDate,
  getDegreeLabel,
} from '@/utils/formatters';
import styles from './TeacherPage.module.scss';

const { Title, Text } = Typography;

export default function TeacherDashboardPage() {
  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ['teacher', 'profile'],
    queryFn: teacherApi.getProfile,
    staleTime: 5 * 60 * 1000,
  });

  const { data: mySectionsResp, isLoading: sectionsLoading } = useQuery({
    queryKey: ['teacher', 'my-sections'],
    queryFn: teacherClassSectionApi.getMyTeaching,
    staleTime: 2 * 60 * 1000,
  });

  const mySections = Array.isArray(mySectionsResp)
    ? mySectionsResp
    : (mySectionsResp?.items || []);

  const openSections = mySections.filter((s) => s.TrangThaiLop === 'Mo');

  const sectionColumns = [
    {
      title: 'Mã lớp HP',
      dataIndex: 'MaLopHP',
      key: 'MaLopHP',
      width: 140,
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
      title: 'Cơ sở',
      dataIndex: 'MaCoSo',
      key: 'MaCoSo',
      width: 120,
      render: (coso) => <Tag color="blue">{getBranchLabel(coso)}</Tag>,
    },
    {
      title: 'Sĩ số',
      key: 'SiSo',
      width: 100,
      align: 'center',
      render: (_, record) => `${record.SiSoHienTai ?? 0}/${record.SiSoToiDa ?? 0}`,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThaiLop',
      key: 'TrangThaiLop',
      width: 90,
      align: 'center',
      render: (status) => {
        const props = getClassSectionStatusProps(status);
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
                  {buildFullName(user.Ho, user.Ten)?.charAt(0)?.toUpperCase() || 'G'}
                </span>
              </div>
              <div className={styles.welcomeText}>
                <Title level={3} className={styles.welcomeTitle}>
                  Xin chào, {buildFullName(user.Ho, user.Ten)}!
                </Title>
                <Text type="secondary" className={styles.welcomeSubtitle}>
                  Mã giảng viên: <strong>{user.MaGV || user.UserId || user.userId}</strong>
                  {user.MaCoSo && <> · {getBranchLabel(user.MaCoSo)}</>}
                </Text>
              </div>
            </>
          ) : null}
        </div>
      </div>

      {/* Stats Row */}
      <Row gutter={[16, 16]} className={styles.statsRow}>
        <Col xs={24} sm={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="Lớp đang phụ trách"
              value={openSections.length}
              prefix={<BookOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="Tổng lớp học phần"
              value={mySections.length}
              prefix={<TeamOutlined style={{ color: '#1677ff' }} />}
              valueStyle={{ color: '#1677ff', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="Tổng sinh viên"
              value={mySections.reduce((sum, s) => sum + (s.SiSoHienTai || 0), 0)}
              prefix={<TeamOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a', fontWeight: 600 }}
            />
          </Card>
        </Col>
      </Row>

      {/* Teacher Info Card */}
      {!userLoading && user && (
        <Card
          title={
            <Space>
              <UserOutlined style={{ color: '#722ed1' }} />
              Thông tin giảng viên
            </Space>
          }
          className={styles.infoCard}
          extra={
            <Link to="/teacher/profile">
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
                <Text type="secondary" className={styles.infoLabel}>Mã giảng viên</Text>
                <Text className={styles.infoValue}>{user.MaGV || '—'}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Học vị</Text>
                <Text className={styles.infoValue}>{getDegreeLabel(user.HocVi)}</Text>
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
                <Text type="secondary" className={styles.infoLabel}>Cơ sở</Text>
                <Text className={styles.infoValue}>{getBranchLabel(user.MaCoSo)}</Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className={styles.infoItem}>
                <Text type="secondary" className={styles.infoLabel}>Trạng thái</Text>
                {(() => {
                  const sp = getTeacherStatusProps(user.TrangThai);
                  return <Tag color={sp.color}>{sp.label}</Tag>;
                })()}
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* My Class Sections */}
      <Card
        title={
          <Space>
            <BookOutlined style={{ color: '#722ed1' }} />
            Lớp học phần của tôi
          </Space>
        }
        extra={
          <Link to="/teacher/class-sections">
            <Button type="link" icon={<RightOutlined />}>Xem tất cả</Button>
          </Link>
        }
        className={styles.recentCard}
      >
        {sectionsLoading ? (
          <Skeleton active paragraph={{ rows: 3 }} />
        ) : mySections.length > 0 ? (
          <Table
            dataSource={mySections.slice(0, 5)}
            columns={sectionColumns}
            rowKey="MaLopHP"
            pagination={false}
            size="middle"
          />
        ) : (
          <Empty
            description="Bạn chưa được phân công lớp học phần nào"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>
    </div>
  );
}
