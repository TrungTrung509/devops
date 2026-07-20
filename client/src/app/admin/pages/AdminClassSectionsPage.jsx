/**
 * Admin Class Sections Page - CRUD for class sections + schedules + enrollments view
 * Supports filtering by: keyword (debounced), MaCoSo, HinhThucHoc, TrangThaiLop
 */

import { useState, useRef } from 'react';
import {
  Card, Table, Button, Space, Tag, Typography, Modal, Form, Input, Select,
  Popconfirm, message, Drawer, Descriptions, Empty, Tabs, Row, Col, Popover,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, ReloadOutlined,
  CalendarOutlined, TeamOutlined, BarChartOutlined, UnorderedListOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { classSectionApi } from '@/services/admin/classSectionApi';
import { courseApi } from '@/services/admin/courseApi';
import { semesterApi } from '@/services/admin/semesterApi';
import { branchApi } from '@/services/admin/branchApi';
import { teacherApi } from '@/services/admin/teacherApi';
import {
  formatDate,
  getWeekdayLabel,
  getWeekdayColor,
  formatLessonTime,
  buildSchedulePopoverItem,
} from '@/utils/formatters';
import EntityOverviewDashboard from '../components/EntityOverviewDashboard';
import { useAdminEntityOverview } from '@/hooks/useAdminOverview';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './AdminPage.module.scss';

const { Title, Text } = Typography;

const STUDY_FORM_OPTIONS = [
  { label: 'Offline', value: 'Offline' },
  { label: 'Online', value: 'Online' },
  { label: 'Hybrid', value: 'Hybrid' },
];

const SECTION_STATUS_OPTIONS = [
  { label: 'Mở', value: 'Mo' },
  { label: 'Đóng', value: 'Dong' },
  { label: 'Hủy', value: 'Huy' },
];

const DEBOUNCE_MS = 400;

export default function AdminClassSectionsPage() {
  const [form] = Form.useForm();
  const [editRecord, setEditRecord] = useState(null);
  const [detailRecord, setDetailRecord] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [pageTab, setPageTab] = useState('info');

  // --- Filter state ---
  const [keyword, setKeyword] = useState('');
  const [debouncedKeyword, setDebouncedKeyword] = useState('');
  const [MaCoSo, setMaCoSo] = useState(null);
  const [HinhThucHoc, setHinhThucHoc] = useState(null);
  const [TrangThaiLop, setTrangThaiLop] = useState(null);
  const [tablePage, setTablePage] = useState(1);

  // Debounce keyword input
  const debounceTimer = useRef(null);
  const handleKeywordChange = (e) => {
    const val = e.target.value;
    setKeyword(val);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setDebouncedKeyword(val);
      setTablePage(1);
    }, DEBOUNCE_MS);
  };

  // Build API params from current filter state
  const apiParams = {
    ...(debouncedKeyword && { keyword: debouncedKeyword }),
    ...(MaCoSo && { MaCoSo }),
    ...(HinhThucHoc && { HinhThucHoc }),
    ...(TrangThaiLop && { TrangThaiLop }),
  };

  // Reset page to 1 whenever a non-keyword filter changes
  const handleSelectChange = (setter) => (val) => {
    setter(val);
    setTablePage(1);
  };

  // ── Overview query
  const { data: overviewData, isLoading: isOverviewLoading, isError: isOverviewError, refetch: refetchOverview } =
    useAdminEntityOverview('class-sections');

  const queryClient = useQueryClient();

  const { data: sectionData, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-class-sections', apiParams],
    queryFn: () => classSectionApi.getAll(apiParams),
  });

  // Backend returns: { items: Section[], total: int }
  const sections = sectionData?.items || sectionData || [];
  const totalSections = sectionData?.total ?? 0;

  const { data: courseData } = useQuery({
    queryKey: ['admin-courses-section'],
    queryFn: courseApi.getAll,
  });
  const courses = courseData?.items || courseData || [];

  const { data: semesterData } = useQuery({
    queryKey: ['admin-semesters-section'],
    queryFn: semesterApi.getAll,
  });
  const semesters = semesterData?.items || semesterData || [];

  const { data: branchData } = useQuery({
    queryKey: ['admin-branches-section'],
    queryFn: branchApi.getAll,
  });
  const branches = branchData?.items || branchData || [];

  const { data: teacherData } = useQuery({
    queryKey: ['admin-teachers-section'],
    queryFn: () => teacherApi.getAll(),
  });
  const teachers = teacherData?.items || teacherData || [];

  const { data: sectionDetail } = useQuery({
    queryKey: ['admin-section-detail', detailRecord?.MaLopHP],
    queryFn: () => classSectionApi.getById(detailRecord.MaLopHP),
    enabled: !!detailRecord?.MaLopHP && drawerOpen,
  });

  const { data: sectionSchedules = [] } = useQuery({
    queryKey: ['admin-section-schedules', detailRecord?.MaLopHP],
    queryFn: () => classSectionApi.getSchedules(detailRecord.MaLopHP),
    enabled: !!detailRecord?.MaLopHP && drawerOpen && pageTab === 'schedules',
  });

  const { data: sectionEnrollments = [] } = useQuery({
    queryKey: ['admin-section-enrollments', detailRecord?.MaLopHP],
    queryFn: () => classSectionApi.getEnrollments(detailRecord.MaLopHP),
    enabled: !!detailRecord?.MaLopHP && drawerOpen && pageTab === 'enrollments',
  });

  const createMutation = useMutation({
    mutationFn: classSectionApi.create,
    onSuccess: () => {
      message.success('Tạo lớp học phần thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-class-sections'] });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Tạo lớp học phần thất bại. Vui lòng thử lại.')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ MaLopHP, data }) => classSectionApi.update(MaLopHP, data),
    onSuccess: () => {
      message.success('Cập nhật thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-class-sections'] });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Cập nhật lớp học phần thất bại. Vui lòng thử lại.')),
  });

  const deleteMutation = useMutation({
    mutationFn: classSectionApi.delete,
    onSuccess: () => {
      message.success('Xóa lớp học phần thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-class-sections'] });
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Xóa lớp học phần thất bại. Vui lòng thử lại.')),
  });

  const handleOpenEdit = (record) => {
    setEditRecord(record);
    form.setFieldsValue({
      MaLopHP: record.MaLopHP,
      MaHocPhan: record.MaHocPhan,
      MaHocKy: record.MaHocKy,
      MaCoSo: record.MaCoSo,
      MaGV: record.MaGV,
      SiSoToiDa: record.SiSoToiDa,
      HinhThucHoc: record.HinhThucHoc,
      TrangThaiLop: record.TrangThaiLop,
    });
    setModalOpen(true);
  };

  const handleOpenCreate = () => {
    setEditRecord(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setEditRecord(null);
    setModalOpen(false);
    form.resetFields();
  };

  const handleSubmit = (values) => {
    if (editRecord) {
      updateMutation.mutate({ MaLopHP: editRecord.MaLopHP, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDetail = (record) => {
    setDetailRecord(record);
    setDrawerOpen(true);
    setPageTab('info');
  };

  const getStatusProps = (status) => {
    const map = { Mo: { color: 'success', label: 'Mở' }, Dong: { color: 'warning', label: 'Đóng' }, Huy: { color: 'error', label: 'Hủy' } };
    return map[status] || { color: 'default', label: status || '—' };
  };

  const columns = [
    {
      title: 'Mã LHP',
      dataIndex: 'MaLopHP',
      key: 'MaLopHP',
      width: 120,
      render: (code) => <Text strong code>{code}</Text>,
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
      width: 100,
      render: (v) => <Tag color="blue">{v || '—'}</Tag>,
    },
    {
      title: 'Giảng viên',
      dataIndex: 'TenGiangVien',
      key: 'TenGiangVien',
      width: 120,
      render: (v) => v || '—',
    },
    {
      title: 'Sĩ số',
      key: 'siSo',
      width: 90,
      render: (_, record) => `${record.SiSoHienTai ?? 0}/${record.SiSoToiDa ?? 0}`,
    },
    {
      title: 'Hình thức',
      dataIndex: 'HinhThucHoc',
      key: 'HinhThucHoc',
      width: 100,
      render: (v) => <Tag>{v || '—'}</Tag>,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThaiLop',
      key: 'TrangThaiLop',
      width: 90,
      render: (s) => {
        const p = getStatusProps(s);
        return <Tag color={p.color}>{p.label}</Tag>;
      },
    },
    {
      title: 'Lịch học',
      key: 'lichHoc',
      width: 150,
      render: (_, record) => {
        const lichHoc = record.LichHoc || [];

        // Lop khong co lich
        if (lichHoc.length === 0) {
          return <Tag color="default">Chưa có lịch</Tag>;
        }

        // Mot lich hoc -> hien thi truc tiep voi gio thuc
        if (lichHoc.length === 1) {
          const item = lichHoc[0];
          const thuLabel = getWeekdayLabel(item.ThuTrongTuan);
          const timeRange = formatLessonTime(item.TietBatDau, item.SoTiet);
          return (
            <Space direction="vertical" size={3} style={{ width: '100%' }}>
              <Space size={4}>
                <Tag color={getWeekdayColor(item.ThuTrongTuan)}>{thuLabel}</Tag>
              </Space>
              <Text style={{ fontSize: 12, color: '#1677ff', fontWeight: 500 }}>
                {timeRange}
              </Text>
              <Text type="secondary" style={{ fontSize: 11 }}>
                {item.TenPhong || item.MaPhong || '—'}
              </Text>
            </Space>
          );
        }

        // Nhieu lich hoc -> Popover
        const sorted = [...lichHoc].sort((a, b) => {
          if (a.ThuTrongTuan !== b.ThuTrongTuan) return a.ThuTrongTuan - b.ThuTrongTuan;
          return a.TietBatDau - b.TietBatDau;
        });

        const popoverContent = (
          <div style={{ minWidth: 280 }}>
            <Text strong style={{ display: 'block', marginBottom: 10, fontSize: 13, color: '#1d39c4' }}>
              {sorted.length} buoi hoc
            </Text>
            {sorted.map((item, idx) => {
              const { thuLabel, weekdayColor, timeRange, phong, ghiChu } = buildSchedulePopoverItem(item);
              return (
                <div
                  key={item.MaLich || idx}
                  style={{
                    padding: '8px 0',
                    borderBottom: idx < sorted.length - 1 ? '1px solid #f0f0f0' : 'none',
                  }}
                >
                  <Space direction="vertical" size={3}>
                    <Space size={4}>
                      <Tag color={weekdayColor}>{thuLabel}</Tag>
                      <Text style={{ fontSize: 12, color: '#1677ff', fontWeight: 500 }}>
                        {timeRange}
                      </Text>
                    </Space>
                    <Text style={{ fontSize: 12 }}>
                      <Text type="secondary">Phong: </Text>
                      {phong}
                    </Text>
                    <Text style={{ fontSize: 12 }}>
                      <Text type="secondary">Ngay: </Text>
                      {item.NgayBatDau && item.NgayKetThuc
                        ? `${formatDate(item.NgayBatDau)} — ${formatDate(item.NgayKetThuc)}`
                        : '—'}
                    </Text>
                    {ghiChu && (
                      <Text type="secondary" style={{ fontSize: 12, fontStyle: 'italic' }}>
                        {ghiChu}
                      </Text>
                    )}
                  </Space>
                </div>
              );
            })}
          </div>
        );

        return (
          <Popover
            content={popoverContent}
            title="Lich hoc cua lop"
            trigger="click"
            placement="left"
            overlayStyle={{ maxWidth: 340 }}
          >
            <Tag
              color="processing"
              style={{ cursor: 'pointer', userSelect: 'none' }}
            >
              {lichHoc.length} buoi hoc
            </Tag>
          </Popover>
        );
      },
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 140,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button type="text" icon={<EyeOutlined />} onClick={() => handleDetail(record)} />
          <Button type="text" icon={<EditOutlined />} onClick={() => handleOpenEdit(record)} />
          <Popconfirm title="Xác nhận xóa lớp học phần?" onConfirm={() => deleteMutation.mutate(record.MaLopHP)} okText="Xóa" cancelText="Hủy" okButtonProps={{ danger: true }}>
            <Button type="text" danger icon={<DeleteOutlined />} loading={deleteMutation.isPending} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const scheduleColumns = [
    {
      title: 'Mã lịch',
      dataIndex: 'MaLich',
      key: 'MaLich',
      width: 90,
      render: (c) => <Text code>{c}</Text>,
    },
    {
      title: 'Thứ',
      dataIndex: 'ThuTrongTuan',
      key: 'ThuTrongTuan',
      width: 80,
      sorter: (a, b) => a.ThuTrongTuan - b.ThuTrongTuan,
      render: (v) => <Tag color={getWeekdayColor(v)}>{getWeekdayLabel(v)}</Tag>,
    },
    {
      title: 'Giờ',
      key: 'thoiGian',
      width: 130,
      sorter: (a, b) => a.TietBatDau - b.TietBatDau,
      render: (_, r) => {
        const timeRange = formatLessonTime(r.TietBatDau, r.SoTiet);
        return <Text style={{ color: '#1677ff', fontWeight: 500, fontSize: 12 }}>{timeRange}</Text>;
      },
    },
    {
      title: 'Tiết',
      key: 'tiet',
      width: 80,
      render: (_, r) => {
        const end = r.SoTiet > 1 ? `${r.TietBatDau}–${r.TietBatDau + r.SoTiet - 1}` : `${r.TietBatDau}`;
        return <Tag color="blue">{end}</Tag>;
      },
    },
    {
      title: 'Phòng',
      dataIndex: 'TenPhong',
      key: 'TenPhong',
      width: 100,
      render: (v, r) => v || r.MaPhong || '—',
    },
    {
      title: 'Từ ngày',
      dataIndex: 'NgayBatDau',
      key: 'NgayBatDau',
      render: (d) => formatDate(d),
    },
    {
      title: 'Đến ngày',
      dataIndex: 'NgayKetThuc',
      key: 'NgayKetThuc',
      render: (d) => formatDate(d),
    },
  ];

  const enrollmentColumns = [
    {
      title: 'Mã ĐK',
      dataIndex: 'MaDangKy',
      key: 'MaDangKy',
      width: 80,
      render: (c) => <Text code>{c}</Text>,
    },
    {
      title: 'Mã SV',
      dataIndex: 'MaSV',
      key: 'MaSV',
      width: 100,
    },
    {
      title: 'Họ tên',
      dataIndex: 'HoTenSinhVien',
      key: 'HoTenSinhVien',
      ellipsis: true,
    },
    {
      title: 'Ngày đăng ký',
      dataIndex: 'NgayDangKy',
      key: 'NgayDangKy',
      render: (d) => formatDate(d),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThaiDangKy',
      key: 'TrangThaiDangKy',
      render: (s) => {
        const map = { DaDangKy: { color: 'processing', label: 'Đã đăng ký' }, HoanThanh: { color: 'success', label: 'Hoàn thành' }, DaHuy: { color: 'error', label: 'Đã hủy' } };
        const p = map[s] || { color: 'default', label: s || '—' };
        return <Tag color={p.color}>{p.label}</Tag>;
      },
    },
  ];

  return (
    <div className={styles.page}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'overview',
            label: (
              <span>
                <BarChartOutlined />
                Tổng quan
              </span>
            ),
            children: (
              <EntityOverviewDashboard
                entity="class-sections"
                data={overviewData}
                loading={isOverviewLoading}
                error={isOverviewError}
                refetch={refetchOverview}
              />
            ),
          },
          {
            key: 'list',
            label: (
              <span>
                <UnorderedListOutlined />
                Danh sách
              </span>
            ),
            children: (
              <>
                <div className={styles.pageHeader}>
                  <div>
                    <Title level={3} className={styles.pageTitle}>Quản lý Lớp học phần</Title>
                    <Text type="secondary">Danh sách và quản lý các lớp học phần</Text>
                  </div>
                  <Space wrap>
                    <Input.Search
                      placeholder="Tìm theo mã, tên..."
                      onChange={handleKeywordChange}
                      onSearch={handleKeywordChange}
                      style={{ width: 200 }}
                      allowClear
                    />
                    <Select
                      placeholder="Cơ sở"
                      allowClear
                      style={{ width: 160 }}
                      value={MaCoSo}
                      onChange={handleSelectChange(setMaCoSo)}
                    >
                      {branches.map((b) => (
                        <Select.Option key={b.MaCoSo} value={b.MaCoSo}>
                          {b.TenCoSo}
                        </Select.Option>
                      ))}
                    </Select>
                    <Select
                      placeholder="Hình thức học"
                      allowClear
                      style={{ width: 150 }}
                      value={HinhThucHoc}
                      onChange={handleSelectChange(setHinhThucHoc)}
                    >
                      {STUDY_FORM_OPTIONS.map((o) => (
                        <Select.Option key={o.value} value={o.value}>
                          {o.label}
                        </Select.Option>
                      ))}
                    </Select>
                    <Select
                      placeholder="Trạng thái"
                      allowClear
                      style={{ width: 120 }}
                      value={TrangThaiLop}
                      onChange={handleSelectChange(setTrangThaiLop)}
                    >
                      {SECTION_STATUS_OPTIONS.map((o) => (
                        <Select.Option key={o.value} value={o.value}>
                          {o.label}
                        </Select.Option>
                      ))}
                    </Select>
                    <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
                      Làm mới
                    </Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
                      Thêm lớp HP
                    </Button>
                  </Space>
                </div>

                <Card className={styles.tableCard}>
                  {isError ? (
                    <Empty description={<Text type="danger">Không thể tải danh sách lớp học phần</Text>} />
                  ) : (
                    <Table
                      dataSource={sections}
                      columns={columns}
                      rowKey="MaLopHP"
                      loading={isLoading}
                      pagination={{
                        current: tablePage,
                        pageSize: 10,
                        showSizeChanger: true,
                        showTotal: (t) => `Tổng ${t} lớp HP`,
                        total: totalSections,
                        onChange: (page) => setTablePage(page),
                      }}
                      scroll={{ x: 1300 }}
                    />
                  )}
                </Card>
              </>
            ),
          },
        ]}
      />

      {/* Create / Edit Modal */}
      <Modal
        title={editRecord ? 'Sửa lớp học phần' : 'Thêm lớp học phần mới'}
        open={modalOpen}
        onCancel={handleCloseModal}
        footer={null}
        width={560}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="MaLopHP" label="Mã lớp HP" rules={[{ required: true, message: 'Vui lòng nhập mã LHP' }]}>
            <Input placeholder="VD: CS101-01" disabled={!!editRecord} maxLength={30} />
          </Form.Item>
          <Form.Item name="MaHocPhan" label="Mã học phần" rules={[{ required: true, message: 'Vui lòng nhập mã HP' }]}>
            <Select showSearch allowClear placeholder="Chọn học phần" optionFilterProp="children">
              {courses.map((c) => <Select.Option key={c.MaHocPhan} value={c.MaHocPhan}>{c.MaHocPhan} - {c.TenHocPhan}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="MaHocKy" label="Học kỳ" rules={[{ required: true, message: 'Vui lòng chọn học kỳ' }]}>
            <Select showSearch allowClear placeholder="Chọn học kỳ" optionFilterProp="children">
              {semesters.map((s) => <Select.Option key={s.MaHocKy} value={s.MaHocKy}>{s.MaHocKy} - HK{s.KySo}/{s.NamHoc}</Select.Option>)}
            </Select>
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="MaCoSo" label="Cơ sở" rules={[{ required: true, message: 'Vui lòng chọn cơ sở' }]}>
                <Select allowClear placeholder="Chọn cơ sở">
                  {branches.map((b) => <Select.Option key={b.MaCoSo} value={b.MaCoSo}>{b.TenCoSo}</Select.Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="MaGV" label="Giảng viên">
                <Select allowClear showSearch placeholder="Chọn giảng viên" optionFilterProp="children">
                  {teachers.map((t) => <Select.Option key={t.MaGV} value={t.MaGV}>{t.MaGV} - {[t.Ho, t.Ten].filter(Boolean).join(' ')}</Select.Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="SiSoToiDa" label="Sĩ số tối đa">
                <Input type="number" placeholder="VD: 50" min={1} max={500} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="HinhThucHoc" label="Hình thức học">
                <Select placeholder="Chọn hình thức" allowClear>
                  {STUDY_FORM_OPTIONS.map((o) => <Select.Option key={o.value} value={o.value}>{o.label}</Select.Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="TrangThaiLop" label="Trạng thái">
            <Select>
              {SECTION_STATUS_OPTIONS.map((o) => <Select.Option key={o.value} value={o.value}>{o.label}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={handleCloseModal}>Hủy</Button>
              <Button type="primary" htmlType="submit" loading={createMutation.isPending || updateMutation.isPending}>
                {editRecord ? 'Cập nhật' : 'Tạo mới'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Detail Drawer */}
      <Drawer
        title={`Chi tiết lớp HP: ${detailRecord?.MaLopHP || ''}`}
        placement="right"
        width={560}
        onClose={() => { setDrawerOpen(false); setDetailRecord(null); }}
        open={drawerOpen}
      >
        <Tabs
          activeKey={pageTab}
          onChange={setPageTab}
          items={[
            {
              key: 'info',
              label: <span><CalendarOutlined /> Thông tin</span>,
              children: sectionDetail ? (
                <Descriptions column={1} bordered size="small">
                  <Descriptions.Item label="Mã LHP"><Text strong code>{sectionDetail.MaLopHP}</Text></Descriptions.Item>
                  <Descriptions.Item label="Học phần">{sectionDetail.TenHocPhan || '—'}</Descriptions.Item>
                  <Descriptions.Item label="Học kỳ">{sectionDetail.MaHocKy || '—'}</Descriptions.Item>
                  <Descriptions.Item label="Cơ sở"><Tag color="blue">{sectionDetail.MaCoSo || '—'}</Tag></Descriptions.Item>
                  <Descriptions.Item label="Giảng viên">{sectionDetail.TenGiangVien || sectionDetail.MaGV || '—'}</Descriptions.Item>
                  <Descriptions.Item label="Sĩ số">{sectionDetail.SiSoHienTai ?? 0} / {sectionDetail.SiSoToiDa ?? 0}</Descriptions.Item>
                  <Descriptions.Item label="Hình thức">{sectionDetail.HinhThucHoc || '—'}</Descriptions.Item>
                  <Descriptions.Item label="Trạng thái">
                    {(() => { const p = getStatusProps(sectionDetail.TrangThaiLop); return <Tag color={p.color}>{p.label}</Tag>; })()}
                  </Descriptions.Item>
                </Descriptions>
              ) : <Empty />
            },
            {
              key: 'schedules',
              label: <span><CalendarOutlined /> Lịch học</span>,
              children: (sectionDetail?.LichHoc && sectionDetail.LichHoc.length > 0)
                ? (
                  <Table
                    dataSource={sectionDetail.LichHoc}
                    columns={scheduleColumns}
                    rowKey="MaLich"
                    size="small"
                    pagination={false}
                    scroll={{ x: 600 }}
                  />
                )
                : sectionSchedules.length > 0
                ? (
                  <Table
                    dataSource={sectionSchedules}
                    columns={scheduleColumns}
                    rowKey="MaLich"
                    size="small"
                    pagination={false}
                    scroll={{ x: 600 }}
                  />
                )
                : <Empty description="Chưa có lịch học" />,
            },
            {
              key: 'enrollments',
              label: <span><TeamOutlined /> SV đăng ký</span>,
              children: sectionEnrollments.length > 0 ? (
                <Table dataSource={sectionEnrollments} columns={enrollmentColumns} rowKey="MaDangKy" size="small" pagination={{ pageSize: 5 }} />
              ) : <Empty description="Chưa có sinh viên đăng ký" />,
            },
          ]}
        />
      </Drawer>
    </div>
  );
}
