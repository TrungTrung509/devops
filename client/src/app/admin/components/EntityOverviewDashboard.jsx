/**
 * EntityOverviewDashboard - Component tong hop hien thi dashboard thong ke
 * Dung chung cho 6 module admin: GiangVien, SinhVien, HocPhan, HocKy, PhongHoc, LopHocPhan
 *
 * Props:
 *   entity       - string: ten entity (teachers | students | courses | semesters | classrooms | class-sections)
 *   data         - object: response tu API /reports/admin-overview/{entity}
 *   loading      - boolean: dang tai
 *   error        - Error: loi API
 *   refetch      - function: goi lai API
 */

import { useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Progress,
  Tag,
  Typography,
  Spin,
  Alert,
  Empty,
  Tooltip,
  Skeleton,
} from 'antd';
import {
  TeamOutlined,
  UserOutlined,
  BookOutlined,
  CalendarOutlined,
  HomeOutlined,
  ReadOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  DesktopOutlined,
} from '@ant-design/icons';
import styles from './EntityOverviewDashboard.module.scss';

const { Title, Text, Paragraph } = Typography;

// Map entity -> icon + mau chu de
const ENTITY_CONFIG = {
  teachers: {
    icon: <TeamOutlined />,
    color: '#1677ff',
    bgColor: '#e6f4ff',
  },
  students: {
    icon: <UserOutlined />,
    color: '#52c41a',
    bgColor: '#f6ffed',
  },
  courses: {
    icon: <BookOutlined />,
    color: '#722ed1',
    bgColor: '#f9f0ff',
  },
  semesters: {
    icon: <CalendarOutlined />,
    color: '#fa8c16',
    bgColor: '#fff7e6',
  },
  classrooms: {
    icon: <HomeOutlined />,
    color: '#13c2c2',
    bgColor: '#e6fffb',
  },
  'class-sections': {
    icon: <ReadOutlined />,
    color: '#eb2f96',
    bgColor: '#fff0f6',
  },
};

function SiteCard({ site, siteName, count, percentage, totalColor }) {
  return (
    <Card
      size="small"
      className={styles.siteCard}
      styles={{ body: { padding: '16px' } }}
    >
      <div className={styles.siteCardInner}>
        <div className={styles.siteCardHeader}>
          <Text strong className={styles.siteName}>{siteName}</Text>
          <Tag color="blue" style={{ fontSize: 11 }}>{site}</Tag>
        </div>
        <div className={styles.siteCardStats}>
          <Title level={3} className={styles.siteCount} style={{ color: totalColor }}>
            {count.toLocaleString()}
          </Title>
          <Text type="secondary" style={{ fontSize: 12 }}>
            bản ghi
          </Text>
        </div>
        <Progress
          percent={percentage}
          size="small"
          strokeColor={totalColor}
          showInfo={false}
          className={styles.siteProgress}
        />
        <Text type="secondary" className={styles.sitePercent}>
          {percentage.toFixed(1)}%
        </Text>
      </div>
    </Card>
  );
}

function StatusBadge({ status, label, count, index }) {
  const colors = ['success', 'processing', 'warning', 'error', 'default', 'purple'];
  const color = colors[index % colors.length];
  return (
    <div className={styles.statusItem}>
      <Tag color={color}>{label}</Tag>
      <Text strong style={{ fontSize: 14 }}>{count.toLocaleString()}</Text>
    </div>
  );
}

function ExtraRow({ statKey, label, count, percentage }) {
  if (!count && count !== 0) return null;
  const isRate = statKey === 'avg_fill_rate' || label.toLowerCase().includes('tỷ lệ') || label.toLowerCase().includes('rate');
  return (
    <div className={styles.extraItem}>
      <Text type="secondary">{label}</Text>
      <div className={styles.extraRight}>
        <Text strong style={{ fontSize: 14, color: '#262626' }}>
          {isRate ? `${count}%` : count.toLocaleString()}
        </Text>
        {percentage != null && (
          <Progress
            percent={percentage}
            size="small"
            strokeColor="#1677ff"
            style={{ width: 80, marginLeft: 8 }}
            showInfo={false}
          />
        )}
      </div>
    </div>
  );
}

export default function EntityOverviewDashboard({ entity, data, loading, error, refetch }) {
  const config = ENTITY_CONFIG[entity] || ENTITY_CONFIG.teachers;

  const hasSiteData = useMemo(() => {
    return data?.by_site?.some((s) => s.site !== 'COMMON' && s.count > 0);
  }, [data]);

  const isCommonData = useMemo(() => {
    return data?.by_site?.length === 1 && data.by_site[0]?.site === 'COMMON';
  }, [data]);

  if (loading) {
    return (
      <div className={styles.wrapper}>
        <Skeleton active paragraph={{ rows: 8 }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.wrapper}>
        <Alert
          type="error"
          message="Không thể tải dữ liệu tổng quan"
          description={error.message || 'Đã xảy ra lỗi khi gọi API. Vui lòng thử lại.'}
          showIcon
          action={
            <button onClick={refetch} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ff4d4f', textDecoration: 'underline' }}>
              Thử lại
            </button>
          }
        />
      </div>
    );
  }

  if (!data || data.total === 0) {
    return (
      <div className={styles.wrapper}>
        <Empty description="Chưa có dữ liệu để hiển thị" />
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      {/* ── Page header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.iconBox} style={{ background: config.bgColor, color: config.color }}>
            <span style={{ fontSize: 24 }}>{config.icon}</span>
          </div>
          <div>
            <Title level={4} style={{ margin: 0 }}>Tổng quan {data.title || entity}</Title>
            <Paragraph type="secondary" style={{ margin: '4px 0 0', fontSize: 13 }}>
              {data.description || 'Thống kê tổng quan toàn trường.'}
            </Paragraph>
          </div>
        </div>
        <div className={styles.headerRight}>
          <Tooltip title="Làm mới dữ liệu">
            <button className={styles.refreshBtn} onClick={refetch}>
              <ReloadOutlined />
            </button>
          </Tooltip>
        </div>
      </div>

      {/* ── Total stat */}
      <Row gutter={[12, 12]}>
        <Col xs={24} sm={8}>
          <Card
            className={styles.totalCard}
            styles={{ body: { padding: '20px 24px' } }}
          >
            <Statistic
              title={
                <Text type="secondary" style={{ fontSize: 13 }}>
                  Tổng số {data.title?.toLowerCase() || entity}
                </Text>
              }
              value={data.total ?? 0}
              prefix={<span style={{ color: config.color }}>{config.icon}</span>}
              valueStyle={{ color: config.color, fontWeight: 700, fontSize: 32 }}
            />
          </Card>
        </Col>

        {/* ── Site breakdown summary */}
        <Col xs={24} sm={16}>
          <Card
            className={styles.summaryCard}
            title={
              <Space size={4}>
                <DesktopOutlined />
                <Text strong>Phân bổ theo cơ sở</Text>
              </Space>
            }
            styles={{ body: { padding: '16px 24px' } }}
            size="small"
          >
            {isCommonData ? (
              <Alert
                type="info"
                message="Dữ liệu dùng chung toàn trường"
                description="Hệ thống này không phân mảnh theo cơ sở. Tất cả bản ghi được quản lý tập trung."
                showIcon
                style={{ margin: 0 }}
              />
            ) : data.by_site?.length > 0 ? (
              <Row gutter={[8, 8]}>
                {data.by_site.map((s, i) => {
                  const colors = ['#1677ff', '#52c41a', '#fa8c16', '#eb2f96'];
                  return (
                    <Col xs={8} sm={8} key={s.site || i}>
                      <div className={styles.miniSite}>
                        <Text type="secondary" style={{ fontSize: 11 }}>{s.site_name}</Text>
                        <Text strong style={{ fontSize: 16, color: colors[i % colors.length] }}>
                          {s.count.toLocaleString()}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>({s.percentage?.toFixed(1)}%)</Text>
                      </div>
                    </Col>
                  );
                })}
              </Row>
            ) : (
              <Text type="secondary">Không có dữ liệu theo cơ sở</Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* ── Detail cards */}
      <Row gutter={[12, 12]}>
        {/* ── Site cards */}
        {!isCommonData && data.by_site?.length > 0 && (
          <>
            {data.by_site.map((s, i) => {
              const colors = ['#1677ff', '#52c41a', '#fa8c16'];
              const color = colors[i % colors.length];
              return (
                <Col xs={24} sm={8} key={s.site || i}>
                  <SiteCard
                    site={s.site}
                    siteName={s.site_name}
                    count={s.count}
                    percentage={s.percentage}
                    totalColor={color}
                  />
                </Col>
              );
            })}
          </>
        )}

        {/* ── Status section */}
        {data.by_status?.length > 0 && (
          <Col xs={24} sm={isCommonData ? 24 : 12}>
            <Card
              className={styles.sectionCard}
              title={
                <Space size={4}>
                  <InfoCircleOutlined />
                  <Text strong>Thống kê theo trạng thái</Text>
                </Space>
              }
              styles={{ body: { padding: '16px 20px' } }}
              size="small"
            >
              <Row gutter={[8, 8]}>
                {data.by_status.map((s, i) => (
                  <Col xs={12} sm={isCommonData ? 8 : 24} key={s.status || i}>
                    <StatusBadge
                      status={s.status}
                      label={s.label}
                      count={s.count}
                      index={i}
                    />
                  </Col>
                ))}
              </Row>
            </Card>
          </Col>
        )}

        {/* ── Extra section */}
        {data.extra?.length > 0 && (
          <Col xs={24} sm={12}>
            <Card
              className={styles.sectionCard}
              title={
                <Space size={4}>
                  <InfoCircleOutlined />
                  <Text strong>Thông tin bổ sung</Text>
                </Space>
              }
              styles={{ body: { padding: '16px 20px' } }}
              size="small"
            >
              {data.extra.map((e, i) => (
                <ExtraRow
                  key={e.key || i}
                  statKey={e.key}
                  label={e.label}
                  count={e.count}
                  percentage={e.percentage}
                />
              ))}
            </Card>
          </Col>
        )}
      </Row>

      {/* ── Summary table */}
      {!isCommonData && data.by_site?.length > 0 && (
        <Card
          className={styles.tableCard}
          title={<Text strong>Chi tiết theo cơ sở</Text>}
          styles={{ body: { padding: 0 } }}
          size="small"
        >
          <Table
            dataSource={data.by_site}
            rowKey="site"
            pagination={false}
            size="small"
            columns={[
              {
                title: 'Mã cơ sở',
                dataIndex: 'site',
                key: 'site',
                width: 140,
                render: (v) => <Tag color="blue">{v}</Tag>,
              },
              {
                title: 'Tên cơ sở',
                dataIndex: 'site_name',
                key: 'site_name',
              },
              {
                title: 'Số lượng',
                dataIndex: 'count',
                key: 'count',
                width: 140,
                align: 'right',
                render: (v) => <Text strong>{v?.toLocaleString()}</Text>,
              },
              {
                title: 'Tỷ lệ',
                dataIndex: 'percentage',
                key: 'percentage',
                width: 200,
                render: (v) => (
                  <Progress
                    percent={v}
                    size="small"
                    strokeColor="#1677ff"
                    format={(val) => `${val?.toFixed(1)}%`}
                  />
                ),
              },
            ]}
          />
        </Card>
      )}
    </div>
  );
}

// Inline helper
function Space({ children, size = 8, ...props }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: size }} {...props}>
      {children}
    </div>
  );
}
