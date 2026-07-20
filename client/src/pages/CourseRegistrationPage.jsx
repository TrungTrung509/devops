/**
 * CourseRegistrationPage - Main enrollment page
 * Layout: Filter/search bar → Table of open class sections → Table of registered enrollments
 */

import { useState, useMemo } from 'react';
import {
  Card,
  Table,
  Input,
  Select,
  Button,
  Space,
  Tag,
  Badge,
  Typography,
  Modal,
  Form,
  Tooltip,
  Skeleton,
  Empty,
  message,
  Popconfirm,
  Row,
  Col,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SwapOutlined,
  InfoCircleOutlined,
  FilterOutlined,
  BookOutlined,
  TeamOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import { useClassSectionsQuery } from '@/hooks/useClassSection';
import { useEnrollmentHistoryQuery, useRegisterEnrollmentMutation, useCancelEnrollmentMutation } from '@/hooks/useEnrollment';
import { useBranchesQuery } from '@/hooks/useMeta';
import {
  getClassSectionStatusProps,
  getEnrollmentStatusProps,
  getStudyFormLabel,
  formatDate,
} from '@/utils/formatters';
import styles from './CourseRegistrationPage.module.scss';

const { Title, Text } = Typography;
const { Search } = Input;

export default function CourseRegistrationPage() {
  const [filters, setFilters] = useState({ keyword: '', maCoSo: null });
  const [registerForm] = Form.useForm();
  const [loadingMaLopHP, setLoadingMaLopHP] = useState(null);

  // Queries
  const { data: classSections = [], isLoading: sectionsLoading, refetch: refetchSections } = useClassSectionsQuery();
  const { data: enrollments = [], isLoading: enrollLoading, refetch: refetchHistory } = useEnrollmentHistoryQuery();
  const { data: branches = [] } = useBranchesQuery();

  // Mutations
  const registerMutation = useRegisterEnrollmentMutation();
  const cancelMutation = useCancelEnrollmentMutation();

  
  // Compute enrolled MaLopHP set for quick lookup
  
  const enrolledMaLopHPs = useMemo(() => {
    const map = new Map();
    enrollments.forEach((e) => {
      if (e.maLopHP) {
        map.set(e.maLopHP, e);
      }
    });
    return map;
  }, [enrollments]);

  
  // Filter class sections (frontend-side filtering)
  
  const filteredSections = useMemo(() => {
    return classSections.filter((sec) => {
      const kw = (filters.keyword || '').toLowerCase().trim();
      if (kw) {
        const matchMaHP = sec.maHocPhan?.toLowerCase().includes(kw);
        const matchTenHP = sec.tenHocPhan?.toLowerCase().includes(kw);
        const matchMaLop = sec.maLopHP?.toLowerCase().includes(kw);
        const matchTenLop = sec.tenLopHP?.toLowerCase().includes(kw);
        if (!matchMaHP && !matchTenHP && !matchMaLop && !matchTenLop) return false;
      }
      if (filters.maCoSo && sec.maCoSo !== filters.maCoSo) return false;
      return true;
    });
  }, [classSections, filters]);

  
  // Active enrollments only (DaDangKy status)
  
  const activeEnrollments = useMemo(() => {
    return enrollments.filter((e) => e.trangThaiDangKy === 'DaDangKy');
  }, [enrollments]);

  
  // Column definitions for OPEN CLASS SECTIONS table
  
  const openSectionColumns = [
    {
      title: 'Mã LHP',
      dataIndex: 'maLopHP',
      key: 'maLopHP',
      width: 110,
      fixed: 'left',
      render: (code) => <Text code style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: 'Mã HP',
      dataIndex: 'maHocPhan',
      key: 'maHocPhan',
      width: 100,
      render: (code) => code || '—',
    },
    {
      title: 'Tên học phần',
      dataIndex: 'tenHocPhan',
      key: 'tenHocPhan',
      width: 200,
      ellipsis: true,
      render: (name) => (
        <Tooltip title={name}>
          <Text ellipsis style={{ maxWidth: 180 }}>
            {name}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: 'Nhóm',
      dataIndex: 'tenLopHP',
      key: 'tenLopHP',
      width: 100,
      render: (v) => v || '—',
    },
    {
      title: 'Cơ sở',
      dataIndex: 'maCoSo',
      key: 'maCoSo',
      width: 120,
      render: (coso) => {
        const map = { HADONG: 'Hà Nội', HOALAC: 'Hòa Lạc', NGOCTRUC: 'Ngọc Trục' };
        return <Tag color="blue">{map[coso] || coso || '—'}</Tag>;
      },
    },
    {
      title: 'Hình thức',
      dataIndex: 'hinhThucHoc',
      key: 'hinhThucHoc',
      width: 100,
      render: (form) => getStudyFormLabel(form),
    },
    {
      title: 'Sĩ số',
      key: 'siSo',
      width: 130,
      align: 'center',
      render: (_, record) => {
        const current = record.siSoHienTai ?? 0;
        const max = record.siSoToiDa ?? 0;
        const remaining = record.soChoConLai ?? (max - current);
        const isFull = remaining <= 0;
        return (
          <Tooltip title={`${current} / ${max} sinh viên`}>
            <div className={styles.siSoCell}>
              <TeamOutlined className={styles.siSoIcon} />
              <Text type={isFull ? 'danger' : undefined} style={{ fontSize: 13 }}>
                {current}/{max}
              </Text>
              {isFull && (
                <Tag color="error" style={{ marginLeft: 4 }}>Full</Tag>
              )}
            </div>
          </Tooltip>
        );
      },
    },
    {
      title: 'Trạng thái',
      dataIndex: 'trangThaiLop',
      key: 'trangThaiLop',
      width: 90,
      align: 'center',
      render: (status) => {
        const props = getClassSectionStatusProps(status);
        return <Tag color={props.color}>{props.label}</Tag>;
      },
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 120,
      fixed: 'right',
      align: 'center',
      render: (_, record) => {
        const enrollment = enrolledMaLopHPs.get(record.maLopHP);
        const isEnrolled = !!enrollment;
        const isFull = (record.soChoConLai ?? (record.siSoToiDa - record.siSoHienTai)) <= 0;
        const isClosed = record.trangThaiLop !== 'Mo';

        if (isEnrolled) {
          return (
            <Tag color="success" icon={<CheckCircleOutlined />}>
              Đã đăng ký
            </Tag>
          );
        }

        if (isClosed) {
          return (
            <Tag color="default" icon={<InfoCircleOutlined />}>
              Đã đóng
            </Tag>
          );
        }

        if (isFull) {
          return (
            <Tag color="error" icon={<InfoCircleOutlined />}>
              Hết chỗ
            </Tag>
          );
        }

        return (
          <Button
            type="primary"
            size="small"
            icon={<CheckCircleOutlined />}
            loading={loadingMaLopHP === record.maLopHP}
            disabled={loadingMaLopHP && loadingMaLopHP !== record.maLopHP}
            onClick={() => handleRegister(record.maLopHP)}
            className={styles.registerBtn}
          >
            Đăng ký
          </Button>
        );
      },
    },
  ];

  
  // Column definitions for REGISTERED ENROLLMENTS table
  
  const enrollmentColumns = [
    {
      title: 'Mã LHP',
      dataIndex: 'maLopHP',
      key: 'maLopHP',
      width: 110,
      render: (code) => <Text code style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: 'Tên học phần',
      dataIndex: 'tenHocPhan',
      key: 'tenHocPhan',
      ellipsis: true,
      render: (name) => (
        <Tooltip title={name}>
          <Text ellipsis style={{ maxWidth: 250 }}>
            {name}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: 'Nhóm',
      dataIndex: 'tenLopHP',
      key: 'tenLopHP',
      width: 100,
      render: (v) => v || '—',
    },
    {
      title: 'Cơ sở',
      dataIndex: 'maCoSo',
      key: 'maCoSo',
      width: 120,
      render: (coso) => {
        const map = { HADONG: 'Hà Nội', HOALAC: 'Hòa Lạc', NGOCTRUC: 'Ngọc Trục' };
        return <Tag color="blue">{map[coso] || coso || '—'}</Tag>;
      },
    },
    {
      title: 'Ngày đăng ký',
      dataIndex: 'ngayDangKy',
      key: 'ngayDangKy',
      width: 140,
      render: (date) => formatDate(date),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'trangThaiDangKy',
      key: 'trangThaiDangKy',
      width: 130,
      align: 'center',
      render: (status) => {
        const props = getEnrollmentStatusProps(status);
        return <Tag color={props.color}>{props.label}</Tag>;
      },
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 120,
      align: 'center',
      render: (_, record) => {
        if (record.trangThaiDangKy !== 'DaDangKy') {
          return <Text type="secondary">—</Text>;
        }
        return (
          <Popconfirm
            title="Xác nhận hủy đăng ký"
            description="Bạn có chắc muốn hủy đăng ký học phần này?"
            onConfirm={() => handleCancelEnrollment(record)}
            okText="Hủy đăng ký"
            cancelText="Không"
            okButtonProps={{ danger: true, loading: cancelMutation.isPending }}
          >
            <Button
              danger
              size="small"
              icon={<CloseCircleOutlined />}
              loading={cancelMutation.isPending}
            >
              Hủy
            </Button>
          </Popconfirm>
        );
      },
    },
  ];

  
  // Register Course Action
  
  const handleRegister = async (maLopHP) => {
    setLoadingMaLopHP(maLopHP);
    try {
      await registerMutation.mutateAsync({
        MaLopHP: maLopHP,
      });
    } catch (err) {
      // Error is handled by mutation onError
    } finally {
      setLoadingMaLopHP(null);
    }
  };

  
  // Cancel Enrollment
  
  const handleCancelEnrollment = async (record) => {
    try {
      await cancelMutation.mutateAsync(record.maLopHP);
    } catch {
      // Error handled by mutation
    }
  };

  
  // Refresh
  
  const handleRefresh = () => {
    refetchSections();
    refetchHistory();
  };

  return (
    <div className={styles.page}>
      {/* Page Title */}
      <div className={styles.pageHeader}>
        <div>
          <Title level={3} className={styles.pageTitle}>Đăng ký môn học</Title>
          <Text type="secondary">
            Chọn lớp học phần từ danh sách bên dưới để đăng ký. Lớp đã đăng ký sẽ hiển thị ở bảng dưới.
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            Làm mới
          </Button>
        </Space>
      </div>

      {/* Filter Bar */}
      <Card className={styles.filterCard} bodyStyle={{ padding: '16px' }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Input
              prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="Tìm mã/tên học phần, mã lớp..."
              allowClear
              value={filters.keyword}
              onChange={(e) => setFilters((f) => ({ ...f, keyword: e.target.value }))}
              size="middle"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="Lọc theo cơ sở"
              allowClear
              style={{ width: '100%' }}
              value={filters.maCoSo}
              onChange={(val) => setFilters((f) => ({ ...f, maCoSo: val }))}
              size="middle"
            >
              {branches.map((b) => (
                <Select.Option key={b.maCoSo} value={b.maCoSo}>
                  {b.tenCoSo}
                </Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={10}>
            <Text type="secondary" className={styles.filterCount}>
              Hiển thị <strong>{filteredSections.length}</strong> lớp học phần
              {activeEnrollments.length > 0 && (
                <> · <Badge status="success" text={`${activeEnrollments.length} đã đăng ký`} /></>
              )}
            </Text>
          </Col>
        </Row>
      </Card>

      {/* Open Class Sections Table */}
      <Card
        className={styles.sectionCard}
        title={
          <Space>
            <BookOutlined style={{ color: '#1677ff' }} />
            <span>Danh sách lớp học phần mở đăng ký</span>
            {!sectionsLoading && (
              <Badge count={filteredSections.length} style={{ backgroundColor: '#1677ff' }} />
            )}
          </Space>
        }
        extra={
          sectionsLoading && <Skeleton.Input size="small" active style={{ width: 80 }} />
        }
      >
        <Table
          columns={openSectionColumns}
          dataSource={filteredSections}
          rowKey="maLopHP"
          loading={sectionsLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} trong ${total} lớp học phần`,
            pageSizeOptions: ['10', '20', '50'],
          }}
          scroll={{ x: 1100 }}
          size="middle"
          rowClassName={(_, index) => index % 2 === 0 ? 'ant-table-row-even' : ''}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="Không có lớp học phần nào phù hợp"
              >
                <Button type="primary" onClick={() => setFilters({ keyword: '', maCoSo: null })}>
                  Xóa bộ lọc
                </Button>
              </Empty>
            ),
          }}
        />
      </Card>

      {/* Registered Enrollments Table */}
      <Card
        className={styles.enrollmentCard}
        title={
          <Space>
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
            <span>Lớp đã đăng ký</span>
            {!enrollLoading && activeEnrollments.length > 0 && (
              <Badge count={activeEnrollments.length} style={{ backgroundColor: '#52c41a' }} />
            )}
          </Space>
        }
        extra={
          enrollLoading && <Skeleton.Input size="small" active style={{ width: 80 }} />
        }
      >
        <Table
          columns={enrollmentColumns}
          dataSource={activeEnrollments}
          rowKey="maDangKy"
          loading={enrollLoading}
          pagination={{
            pageSize: 5,
            showSizeChanger: false,
            showTotal: (total) => `${total} học phần đã đăng ký`,
          }}
          scroll={{ x: 800 }}
          size="middle"
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="Bạn chưa đăng ký lớp nào"
              >
                <Text type="secondary">Chọn lớp từ bảng trên để đăng ký ngay!</Text>
              </Empty>
            ),
          }}
        />
      </Card>


    </div>
  );
}
