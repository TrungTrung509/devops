/**
 * Student Class Sections Page - Browse available class sections and register
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
  BookOutlined,
  TeamOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentClassSectionApi, studentEnrollmentApi } from '@/services/studentApi';
import { semesterApi } from '@/services/semesterApi';
import { branchApi } from '@/services/branchApi';
import {
  getClassSectionStatusProps,
  getEnrollmentStatusProps,
  getStudyFormLabel,
  formatDate,
  getWeekdayLabel,
  getWeekdayColor,
  formatLessonTime,
} from '@/utils/formatters';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './StudentPage.module.scss';

const { Title, Text } = Typography;

export default function StudentClassSectionsPage() {
  const [filters, setFilters] = useState({ keyword: '', MaCoSo: null, MaHocKy: null });
  const [loadingMaLopHP, setLoadingMaLopHP] = useState(null);
  const queryClient = useQueryClient();

  const { data: classSectionsResp, isLoading: sectionsLoading, refetch: refetchSections } = useQuery({
    queryKey: ['student', 'class-sections', filters],
    queryFn: () => studentClassSectionApi.getAvailable(filters),
    staleTime: 2 * 60 * 1000,
  });

  // Unwrap paginated response { items: [], total }
  const classSections = Array.isArray(classSectionsResp)
    ? classSectionsResp
    : (classSectionsResp?.items || []);

  const { data: enrollmentsResp, isLoading: enrollLoading, refetch: refetchHistory } = useQuery({
    queryKey: ['student', 'enrollments'],
    queryFn: () => studentEnrollmentApi.getHistory(),
    staleTime: 2 * 60 * 1000,
  });

  const enrollments = Array.isArray(enrollmentsResp) ? enrollmentsResp : [];

  const { data: semestersResp } = useQuery({
    queryKey: ['meta', 'semesters'],
    queryFn: semesterApi.getAll,
    staleTime: 30 * 60 * 1000,
  });

  const semesters = Array.isArray(semestersResp)
    ? semestersResp
    : (semestersResp?.items || []);

  const { data: branchesResp } = useQuery({
    queryKey: ['meta', 'branches'],
    queryFn: branchApi.getAll,
    staleTime: 30 * 60 * 1000,
  });

  const branches = Array.isArray(branchesResp) ? branchesResp : [];

  const registerMutation = useMutation({
    mutationFn: studentEnrollmentApi.register,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['student', 'class-sections'] });
      queryClient.invalidateQueries({ queryKey: ['student', 'enrollments'] });
      message.success(data?.message || 'Đăng ký thành công!');
    },
    onError: (error) => {
      const msg = getApiErrorMessage(error, 'Đăng ký thất bại. Vui lòng thử lại.');
      message.error(msg);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: studentEnrollmentApi.cancel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student', 'class-sections'] });
      queryClient.invalidateQueries({ queryKey: ['student', 'enrollments'] });
      message.success('Hủy đăng ký thành công!');
    },
    onError: (error) => {
      const msg = getApiErrorMessage(error, 'Hủy đăng ký thất bại. Vui lòng thử lại.');
      message.error(msg);
    },
  });

  // Map of MaLopHP -> enrollment for quick lookup
  const enrolledMap = useMemo(() => {
    const map = new Map();
    enrollments.forEach((e) => {
      if (e.MaLopHP) map.set(e.MaLopHP, e);
    });
    return map;
  }, [enrollments]);

  const filteredSections = useMemo(() => {
    return classSections.filter((sec) => {
      const kw = (filters.keyword || '').toLowerCase().trim();
      if (kw) {
        const matchMaHP = sec.MaHocPhan?.toLowerCase().includes(kw);
        const matchTenHP = sec.TenHocPhan?.toLowerCase().includes(kw);
        const matchMaLop = sec.MaLopHP?.toLowerCase().includes(kw);
        const matchTenLop = sec.TenLopHP?.toLowerCase().includes(kw);
        if (!matchMaHP && !matchTenHP && !matchMaLop && !matchTenLop) return false;
      }
      if (filters.MaCoSo && sec.MaCoSo !== filters.MaCoSo) return false;
      if (filters.MaHocKy && sec.MaHocKy !== filters.MaHocKy) return false;
      return true;
    });
  }, [classSections, filters]);

  const activeEnrollments = useMemo(() => {
    return enrollments.filter((e) => e.TrangThaiDangKy === 'DaDangKy');
  }, [enrollments]);

  const openSectionColumns = [
    {
      title: 'Mã LHP',
      dataIndex: 'MaLopHP',
      key: 'MaLopHP',
      width: 120,
      fixed: 'left',
      render: (code) => <Text code style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: 'Mã HP',
      dataIndex: 'MaHocPhan',
      key: 'MaHocPhan',
      width: 90,
      render: (v) => v || '—',
    },
    {
      title: 'Tên học phần',
      dataIndex: 'TenHocPhan',
      key: 'TenHocPhan',
      width: 200,
      ellipsis: true,
      render: (name) => (
        <Tooltip title={name}>
          <Text ellipsis style={{ maxWidth: 180 }}>{name}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Nhóm',
      dataIndex: 'TenLopHP',
      key: 'TenLopHP',
      width: 90,
      render: (v) => v || '—',
    },
    {
      title: 'Học kỳ',
      dataIndex: 'MaHocKy',
      key: 'MaHocKy',
      width: 90,
    },
    {
      title: 'Cơ sở',
      dataIndex: 'MaCoSo',
      key: 'MaCoSo',
      width: 120,
      render: (MaCoSo) => {
        const branch = branches.find((b) => b.MaCoSo === MaCoSo);
        return <Tag color="blue">{branch?.TenCoSo || MaCoSo || '—'}</Tag>;
      },
    },
    {
      title: 'Giảng viên',
      dataIndex: 'TenGiangVien',
      key: 'TenGiangVien',
      width: 140,
      ellipsis: true,
      render: (v) => v || '—',
    },
    {
      title: 'Hình thức',
      dataIndex: 'HinhThucHoc',
      key: 'HinhThucHoc',
      width: 100,
      render: (form) => getStudyFormLabel(form),
    },
    {
      title: 'Sĩ số',
      key: 'SiSo',
      width: 110,
      align: 'center',
      render: (_, record) => {
        const current = record.SiSoHienTai ?? 0;
        const max = record.SiSoToiDa ?? 0;
        const isFull = current >= max;
        return (
          <Tooltip title={`${current} / ${max} sinh viên`}>
            <Space size={4}>
              <TeamOutlined style={{ color: isFull ? '#ff4d4f' : '#595959' }} />
              <Text type={isFull ? 'danger' : undefined} style={{ fontSize: 13 }}>
                {current}/{max}
              </Text>
            </Space>
          </Tooltip>
        );
      },
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
    {
      title: 'Lịch học',
      key: 'lichHoc',
      width: 280,
      render: (_, record) => {
        const lichHoc = record.LichHoc || [];

        if (lichHoc.length === 0) {
          return <Text type="secondary" style={{ fontSize: 12 }}>Chưa có lịch</Text>;
        }

        // Sap xep: thu tang dan, neu cung thu thi tieu de tang
        const sorted = [...lichHoc].sort((a, b) => {
          if (a.ThuTrongTuan !== b.ThuTrongTuan) return a.ThuTrongTuan - b.ThuTrongTuan;
          return (a.TietBatDau ?? 0) - (b.TietBatDau ?? 0);
        });

        return (
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            {sorted.map((item, idx) => {
              const thuLabel = getWeekdayLabel(item.ThuTrongTuan);
              const weekdayColor = getWeekdayColor(item.ThuTrongTuan);
              const timeRange = formatLessonTime(item.TietBatDau, item.SoTiet);
              const phong = item.TenPhong || item.MaPhong || null;
              const ngayBatDau = item.NgayBatDau ? formatDate(item.NgayBatDau) : null;
              const ngayKetThuc = item.NgayKetThuc ? formatDate(item.NgayKetThuc) : null;
              const hasDateRange = ngayBatDau || ngayKetThuc;
              const ghiChu = item.GhiChu;

              return (
                <div
                  key={item.MaLich || idx}
                  style={{
                    padding: '5px 8px',
                    borderRadius: 6,
                    background: '#f8faff',
                    border: '1px solid #e8f0fe',
                    width: '100%',
                  }}
                >
                  <Space size={6} wrap>
                    <Tag color={weekdayColor} style={{ marginRight: 0 }}>
                      {thuLabel}
                    </Tag>
                    <Text style={{ fontSize: 12, color: '#1677ff', fontWeight: 500 }}>
                      {timeRange}
                    </Text>
                  </Space>
                  {phong && (
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 2 }}>
                      {phong}
                    </Text>
                  )}
                  {hasDateRange && (
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 1 }}>
                      {ngayBatDau}{ngayKetThuc && ngayBatDau !== ngayKetThuc ? ` – ${ngayKetThuc}` : ''}
                    </Text>
                  )}
                  {ghiChu && (
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 1, fontStyle: 'italic' }}>
                      {ghiChu}
                    </Text>
                  )}
                </div>
              );
            })}
          </Space>
        );
      },
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 120,
      fixed: 'right',
      align: 'center',
      render: (_, record) => {
        const enrollment = enrolledMap.get(record.MaLopHP);
        const isEnrolled = !!enrollment;
        const current = record.SiSoHienTai ?? 0;
        const max = record.SiSoToiDa ?? 0;
        const isFull = current >= max;
        const isClosed = record.TrangThaiLop !== 'Mo';

        if (isEnrolled) {
          return <Tag color="success" icon={<CheckCircleOutlined />}>Đã đăng ký</Tag>;
        }
        if (isClosed) return <Tag color="default" icon={<InfoCircleOutlined />}>Đã đóng</Tag>;
        if (isFull) return <Tag color="error" icon={<InfoCircleOutlined />}>Hết chỗ</Tag>;

        return (
          <Button
            type="primary"
            size="small"
            icon={<CheckCircleOutlined />}
            loading={loadingMaLopHP === record.MaLopHP}
            disabled={loadingMaLopHP && loadingMaLopHP !== record.MaLopHP}
            onClick={() => handleRegister(record.MaLopHP)}
          >
            Đăng ký
          </Button>
        );
      },
    },
  ];

  const enrollmentColumns = [
    {
      title: 'Mã LHP',
      dataIndex: 'MaLopHP',
      key: 'MaLopHP',
      width: 120,
      render: (code) => <Text code style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: 'Tên học phần',
      dataIndex: 'TenHocPhan',
      key: 'TenHocPhan',
      ellipsis: true,
      render: (name) => (
        <Tooltip title={name}>
          <Text ellipsis>{name}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Học kỳ',
      dataIndex: 'MaHocKy',
      key: 'MaHocKy',
      width: 90,
    },
    {
      title: 'Cơ sở',
      dataIndex: 'MaCoSo',
      key: 'MaCoSo',
      width: 120,
      render: (MaCoSo) => {
        const branch = branches.find((b) => b.MaCoSo === MaCoSo);
        return <Tag color="blue">{branch?.TenCoSo || MaCoSo || '—'}</Tag>;
      },
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
        if (record.TrangThaiDangKy !== 'DaDangKy') return <Text type="secondary">—</Text>;
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

  const handleCancelEnrollment = async (record) => {
    try {
      await cancelMutation.mutateAsync(record.MaLopHP);
    } catch {}
  };

  const handleRefresh = () => {
    refetchSections();
    refetchHistory();
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <Title level={3} className={styles.pageTitle}>Lớp học phần</Title>
          <Text type="secondary">
            Chọn lớp học phần để đăng ký. Lớp đã đăng ký sẽ hiển thị ở bảng dưới.
          </Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={handleRefresh}>Làm mới</Button>
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
              value={filters.MaCoSo}
              onChange={(val) => setFilters((f) => ({ ...f, MaCoSo: val }))}
              size="middle"
            >
              {branches.map((b) => (
                <Select.Option key={b.MaCoSo} value={b.MaCoSo}>{b.TenCoSo}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="Lọc theo học kỳ"
              allowClear
              style={{ width: '100%' }}
              value={filters.MaHocKy}
              onChange={(val) => setFilters((f) => ({ ...f, MaHocKy: val }))}
              size="middle"
            >
              {semesters.map((s) => (
                <Select.Option key={s.MaHocKy} value={s.MaHocKy}>
                  HK{s.KySo} – {s.NamHoc}
                </Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={4}>
            <Text type="secondary">
              Hiển thị <strong>{filteredSections.length}</strong> lớp
              {activeEnrollments.length > 0 && (
                <> · <Badge status="success" text={`${activeEnrollments.length} đã đăng ký`} /></>
              )}
            </Text>
          </Col>
        </Row>
      </Card>

      {/* Open Class Sections Table */}
      <Card
        title={
          <Space>
            <BookOutlined style={{ color: '#1677ff' }} />
            <span>Danh sách lớp học phần</span>
            {!sectionsLoading && <Badge count={filteredSections.length} style={{ backgroundColor: '#1677ff' }} />}
          </Space>
        }
        extra={sectionsLoading && <Skeleton.Input size="small" active style={{ width: 80 }} />}
      >
        <Table
          columns={openSectionColumns}
          dataSource={filteredSections}
          rowKey="MaLopHP"
          loading={sectionsLoading}
          pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t, r) => `${r[0]}-${r[1]} trong ${t}`, pageSizeOptions: ['10', '20', '50'] }}
          scroll={{ x: 1700 }}
          size="middle"
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Không có lớp học phần nào phù hợp" /> }}
        />
      </Card>

      {/* Registered Enrollments Table */}
      <Card
        title={
          <Space>
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
            <span>Lớp đã đăng ký</span>
            {!enrollLoading && activeEnrollments.length > 0 && <Badge count={activeEnrollments.length} style={{ backgroundColor: '#52c41a' }} />}
          </Space>
        }
        extra={enrollLoading && <Skeleton.Input size="small" active style={{ width: 80 }} />}
      >
        <Table
          columns={enrollmentColumns}
          dataSource={activeEnrollments}
          rowKey="MaDangKy"
          loading={enrollLoading}
          pagination={{ pageSize: 5, showSizeChanger: false, showTotal: (t) => `${t} học phần đã đăng ký` }}
          scroll={{ x: 800 }}
          size="middle"
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Bạn chưa đăng ký lớp nào" /> }}
        />
      </Card>


    </div>
  );
}
