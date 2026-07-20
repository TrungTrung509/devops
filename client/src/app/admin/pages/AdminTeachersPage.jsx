/**
 * Admin Teachers Page - Full CRUD for teachers
 * Backend: GET /teachers/ (list paginated), GET /teachers/{maGV}, POST /teachers/, PUT /teachers/{maGV},
 *         PATCH /teachers/{maGV}/status, DELETE /teachers/{maGV}
 *
 * Teacher fields (PascalCase from backend):
 *   MaGV, Ho, Ten, email(lowercase in schema), SDT, NgaySinh, GioiTinh, DiaChi,
 *   HocVi, HocHam, MaCoSo, MaKhoa, TrangThai, NgayVaoLam, NgayTao, userId
 *
 * TeacherStatus enum: DangCongTac | TamNghi | NghiViec
 * VALID_DEGREES: CN | ThS | TS | PGS
 * Genders: Nam | Nu | Khac
 */

import { useState } from 'react';
import {
  Card, Table, Button, Space, Tag, Typography, Modal, Form, Input, Select,
  Popconfirm, message, Drawer, Descriptions, Empty, Row, Col, Statistic, Tabs
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, ReloadOutlined,
  TeamOutlined, SwapOutlined, BarChartOutlined, UnorderedListOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { teacherApi, teacherKeys } from '@/services/admin/teacherApi';
import { branchApi } from '@/services/admin/branchApi';
import { departmentApi, departmentKeys } from '@/services/admin/departmentApi';
import { formatDate } from '@/utils/formatters';
import EntityOverviewDashboard from '../components/EntityOverviewDashboard';
import { useAdminEntityOverview } from '@/hooks/useAdminOverview';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './AdminPage.module.scss';

const { Title, Text } = Typography;

// ─── Status & Enum Mappings ───────────────────────────────────────────────

const STATUS_MAP = {
  DangCongTac: { color: 'success', label: 'Đang công tác' },
  TamNghi:    { color: 'warning',  label: 'Tạm nghỉ' },
  NghiViec:   { color: 'error',   label: 'Đã nghỉ' },
};

const GENDER_MAP = {
  Nam:  'Nam',
  Nu:   'Nữ',
  Khac: 'Khác',
};

const DEGREE_MAP = {
  CN:  'Cử nhân',
  ThS: 'Thạc sĩ',
  TS:  'Tiến sĩ',
  PGS: 'Phó Giáo sư',
};

const DEGREE_OPTIONS = [
  { label: 'Cử nhân (CN)',      value: 'CN'  },
  { label: 'Thạc sĩ (ThS)',     value: 'ThS' },
  { label: 'Tiến sĩ (TS)',       value: 'TS'  },
  { label: 'Phó Giáo sư (PGS)', value: 'PGS' },
];

const STATUS_OPTIONS = [
  { label: 'Đang công tác', value: 'DangCongTac' },
  { label: 'Tạm nghỉ',      value: 'TamNghi'    },
  { label: 'Đã nghỉ',       value: 'NghiViec'   },
];

const GENDER_OPTIONS = [
  { label: 'Nam',  value: 'Nam'  },
  { label: 'Nữ',   value: 'Nu'   },
  { label: 'Khác', value: 'Khac' },
];

// ─── Helpers ────────────────────────────────────────────────────────────────

function getStatusProps(s) {
  return STATUS_MAP[s] || { color: 'default', label: s || '—' };
}

function getGenderLabel(s) {
  return GENDER_MAP[s] || s || '—';
}

function getDegreeLabel(s) {
  return DEGREE_MAP[s] || s || '—';
}

function toISODateString(value) {
  if (!value) return undefined;
  if (typeof value === 'string') return value.slice(0, 10);
  // moment or dayjs object
  if (typeof value.format === 'function') return value.format('YYYY-MM-DD');
  return String(value);
}

// ─── Component ─────────────────────────────────────────────────────────────

export default function AdminTeachersPage() {
  const queryClient = useQueryClient();
  const [form] = Form.useForm();

  // ── Tab state
  const [activeTab, setActiveTab] = useState('overview');

  // ── Overview query
  const { data: overviewData, isLoading: isOverviewLoading, isError: isOverviewError, refetch: refetchOverview } =
    useAdminEntityOverview('teachers');

  // ── Filter + Pagination state (camelCase for API params)
  const [filters, setFilters] = useState({
    keyword: undefined,
    maCoSo: 'HADONG',
    maKhoa: undefined,
    trangThai: undefined,
    page: 1,
    pageSize: 10,
  });

  // ── Modal / Drawer state
  const [modalOpen, setModalOpen]     = useState(false);
  const [drawerOpen, setDrawerOpen]   = useState(false);
  const [editRecord, setEditRecord]   = useState(null);   // null = create mode
  const [detailRecord, setDetailRecord] = useState(null);

  // ── Query: Teachers (paginated, filters in camelCase for API)
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: teacherKeys.list(filters),
    queryFn: () => teacherApi.getAll(filters),
    select: (res) => ({
      items: res.items || [],
      total: res.total || 0,
      stats: res.stats || {},
    }),
    keepPreviousData: true,
  });

  const teachers  = data?.items || [];
  const total    = data?.total || 0;

  // ── Query: Branches (for dropdown + detail label)
  const { data: branchData } = useQuery({
    queryKey: ['admin', 'branches', 'select'],
    queryFn: () => branchApi.getAll(),
    staleTime: 5 * 60 * 1000,
  });
  const branches = Array.isArray(branchData) ? branchData : (branchData?.items || []);

  // ── Query: Departments (for dropdown)
  const { data: deptData } = useQuery({
    queryKey: departmentKeys.list(),
    queryFn: departmentApi.getAll,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
  const departments = Array.isArray(deptData) ? deptData : [];

  // ── Mutations
  const createMutation = useMutation({
    mutationFn: teacherApi.create,
    onSuccess: () => {
      message.success('Thêm giảng viên thành công!');
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Thêm giảng viên thất bại. Vui lòng thử lại.')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ MaGV, data: payload }) => teacherApi.update(MaGV, payload),
    onSuccess: () => {
      message.success('Cập nhật thành công!');
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Cập nhật giảng viên thất bại. Vui lòng thử lại.')),
  });

  const statusMutation = useMutation({
    mutationFn: ({ MaGV, TrangThai }) => teacherApi.updateStatus(MaGV, TrangThai),
    onSuccess: () => {
      message.success('Đổi trạng thái thành công!');
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Đổi trạng thái giảng viên thất bại. Vui lòng thử lại.')),
  });

  const deleteMutation = useMutation({
    mutationFn: teacherApi.delete,
    onSuccess: () => {
      message.success('Xóa giảng viên thành công!');
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Xóa giảng viên thất bại. Vui lòng thử lại.')),
  });

  // ── Handlers
  const handleOpenCreate = () => {
    setEditRecord(null);
    form.resetFields();
    form.setFieldsValue({ TrangThai: 'DangCongTac' });
    setModalOpen(true);
  };

  const handleOpenEdit = (record) => {
    setEditRecord(record);
    form.setFieldsValue({
      MaGV:       record.MaGV,
      Ho:         record.Ho,
      Ten:         record.Ten,
      email:      record.email ?? record.Email ?? '',
      SDT:        record.SDT,
      NgaySinh:   record.NgaySinh,
      GioiTinh:   record.GioiTinh,
      DiaChi:     record.DiaChi,
      HocVi:      record.HocVi,
      HocHam:     record.HocHam,
      MaCoSo:     record.MaCoSo,
      MaKhoa:     record.MaKhoa,
      TrangThai:  record.TrangThai,
      NgayVaoLam: record.NgayVaoLam,
    });
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditRecord(null);
    form.resetFields();
  };

  const handleSubmit = (values) => {
    const payload = {
      ...values,
      NgaySinh:   toISODateString(values.NgaySinh),
      NgayVaoLam: toISODateString(values.NgayVaoLam),
    };

    if (editRecord) {
      updateMutation.mutate({ MaGV: editRecord.MaGV, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleDetail = (record) => {
    setDetailRecord(record);
    setDrawerOpen(true);
  };

  const handleChangeStatus = (MaGV, newStatus) => {
    if (newStatus === 'NghiViec') {
      Modal.confirm({
        title: 'Xác nhận đổi trạng thái',
        content: 'Chuyển giảng viên sang "Đã nghỉ"? Hành động này sẽ cập nhật trạng thái giảng viên.',
        okText: 'Xác nhận',
        cancelText: 'Hủy',
        onOk: () => statusMutation.mutate({ MaGV, TrangThai: newStatus }),
      });
    } else {
      statusMutation.mutate({ MaGV, TrangThai: newStatus });
    }
  };

  const handleClearFilters = () => {
    setFilters({ keyword: undefined, maCoSo: 'HADONG', maKhoa: undefined, trangThai: undefined, page: 1, pageSize: 10 });
  };

  const handlePageChange = (page, pageSize) => {
    setFilters((f) => ({ ...f, page, pageSize: pageSize ?? f.pageSize }));
  };

  // ── Statistics from data (Backend returns stats: { DangCongTac, TamNghi, NghiViec })
  const stats = {
    total:       total,
    active:       data?.stats?.DangCongTac ?? 0,
    suspended:    data?.stats?.TamNghi ?? 0,
    retired:      data?.stats?.NghiViec ?? 0,
  };

  // ── Table columns
  const columns = [
    {
      title: 'Mã GV',
      dataIndex: 'MaGV',
      key: 'MaGV',
      width: 120,
      fixed: 'left',
      render: (v) => <Text strong code style={{ fontSize: 12 }}>{v}</Text>,
    },
    {
      title: 'Họ tên',
      key: 'hoTen',
      width: 160,
      ellipsis: true,
      render: (_, r) => `${r.Ho || ''} ${r.Ten || ''}`.trim() || '—',
    },
    {
      title: 'Cơ sở',
      dataIndex: 'MaCoSo',
      key: 'MaCoSo',
      width: 110,
      render: (v) => {
        const b = branches.find((b) => b.MaCoSo === v);
        return <Tag color="blue">{b?.TenCoSo || v || '—'}</Tag>;
      },
    },
    {
      title: 'Khoa',
      dataIndex: 'MaKhoa',
      key: 'MaKhoa',
      width: 90,
      render: (v) => {
        const d = departments.find((d) => d.MaKhoa === v);
        return <Text type="secondary">{d ? `${d.MaKhoa} - ${d.TenKhoa}` : v || '—'}</Text>;
      },
    },
    {
      title: 'Học vị',
      dataIndex: 'HocVi',
      key: 'HocVi',
      width: 90,
      render: (v) => <Tag color="purple">{getDegreeLabel(v)}</Tag>,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThai',
      key: 'TrangThai',
      width: 130,
      render: (s) => {
        const p = getStatusProps(s);
        return <Tag color={p.color}>{p.label}</Tag>;
      },
    },
    {
      title: 'Email',
      key: 'email',
      width: 170,
      ellipsis: true,
      render: (_, r) => {
        const email = r.email ?? r.Email ?? '—';
        return <Text type="secondary" style={{ fontSize: 12 }}>{email}</Text>;
      },
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space size={4} wrap>
          <Button type="text" size="small" icon={<EyeOutlined />} onClick={() => handleDetail(record)} title="Chi tiết" />
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleOpenEdit(record)} title="Sửa" />
          {/* <Select
            size="small"
            value={record.TrangThai}
            style={{ width: 110 }}
            onChange={(val) => handleChangeStatus(record.MaGV, val)}
            options={STATUS_OPTIONS}
            variant="borderless"
          /> */}
          <Popconfirm
            title="Xác nhận xóa giảng viên này?"
            description="Hành động không thể hoàn tác."
            onConfirm={() => deleteMutation.mutate(record.MaGV)}
            okText="Xóa" cancelText="Hủy" okButtonProps={{ danger: true }}
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} loading={deleteMutation.isPending} title="Xóa" />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // ── Detail Drawer content
  const renderDrawer = () => {
    if (!detailRecord) return null;
    const r = detailRecord;
    const sp = getStatusProps(r.TrangThai);
    const branch = branches.find((b) => b.MaCoSo === r.MaCoSo);
    const dept  = departments.find((d) => d.MaKhoa === r.MaKhoa);

    return (
      <Descriptions column={1} bordered size="small">
        <Descriptions.Item label="Mã GV">
          <Text strong code>{r.MaGV}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Họ tên">{[r.Ho, r.Ten].filter(Boolean).join(' ') || '—'}</Descriptions.Item>
        <Descriptions.Item label="userId">{r.userId || '—'}</Descriptions.Item>
        <Descriptions.Item label="Email">{r.email ?? r.Email ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="SĐT">{r.SDT || '—'}</Descriptions.Item>
        <Descriptions.Item label="Ngày sinh">{formatDate(r.NgaySinh)}</Descriptions.Item>
        <Descriptions.Item label="Giới tính">{getGenderLabel(r.GioiTinh)}</Descriptions.Item>
        <Descriptions.Item label="Địa chỉ">{r.DiaChi || '—'}</Descriptions.Item>
        <Descriptions.Item label="Cơ sở">
          <Tag color="blue">{branch?.TenCoSo || r.MaCoSo || '—'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Khoa">
          {dept ? `${dept.MaKhoa} - ${dept.TenKhoa}` : r.MaKhoa || '—'}
        </Descriptions.Item>
        <Descriptions.Item label="Học vị">{getDegreeLabel(r.HocVi)}</Descriptions.Item>
        <Descriptions.Item label="Học hàm">{r.HocHam || '—'}</Descriptions.Item>
        <Descriptions.Item label="Trạng thái">
          <Tag color={sp.color}>{sp.label}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Ngày vào làm">{formatDate(r.NgayVaoLam)}</Descriptions.Item>
        <Descriptions.Item label="Ngày tạo">{formatDate(r.NgayTao)}</Descriptions.Item>
      </Descriptions>
    );
  };

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
                entity="teachers"
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
                {/* ── Page Header */}
                <div className={styles.pageHeader}>
                  <div>
                    <Title level={3} className={styles.pageTitle}>Quản lý Giảng viên</Title>
                    <Text type="secondary">Thêm, sửa, xóa và quản lý thông tin giảng viên trong hệ thống</Text>
                  </div>
                  <Space>
                    <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
                      Thêm giảng viên
                    </Button>
                  </Space>
                </div>

                {/* ── Stats Row */}
                <Row gutter={[12, 12]}>
                  {[
                    { label: 'Tổng cứng', value: total,          color: '#1677ff', icon: <TeamOutlined /> },
                    { label: 'Công tác', value: stats.active,    color: '#52c41a', icon: <TeamOutlined /> },
                    { label: 'Tạm nghỉ', value: stats.suspended, color: '#faad14', icon: <TeamOutlined /> },
                    { label: 'Đã nghỉ',  value: stats.retired,   color: '#ff4d4f', icon: <TeamOutlined /> },
                  ].map((s) => (
                    <Col xs={12} sm={6} key={s.label}>
                      <Card size="small" styles={{ body: { padding: '12px 16px' } }}>
                        <Statistic
                          title={<Text type="secondary" style={{ fontSize: 12 }}>{s.label}</Text>}
                          value={isLoading ? '-' : s.value}
                          prefix={<span style={{ color: s.color }}>{s.icon}</span>}
                          valueStyle={{ color: s.color, fontSize: 22, fontWeight: 700 }}
                        />
                      </Card>
                    </Col>
                  ))}
                </Row>

                {/* ── Filter Bar */}
                <Card className={styles.filterCard} styles={{ body: { padding: 16 } }}>
                  <Row gutter={[12, 12]} align="middle">
                    <Col xs={24} sm={12} md={6}>
                      <Input.Search
                        placeholder="Tìm mã GV, họ, tên..."
                        allowClear
                        onSearch={(v) => setFilters((f) => ({ ...f, keyword: v || undefined, page: 1 }))}
                        style={{ width: '100%' }}
                      />
                    </Col>
                    <Col xs={12} sm={6} md={4}>
                      <Select
                        placeholder="Cơ sở"
                        allowClear
                        style={{ width: '100%' }}
                        onChange={(v) => setFilters((f) => ({ ...f, maCoSo: v || undefined, page: 1 }))}
                        value={filters.maCoSo}
                        options={branches.map((b) => ({ label: b.TenCoSo, value: b.MaCoSo }))}
                      />
                    </Col>
                    <Col xs={12} sm={6} md={4}>
                      <Select
                        placeholder="Khoa"
                        allowClear
                        style={{ width: '100%' }}
                        onChange={(v) => setFilters((f) => ({ ...f, maKhoa: v || undefined, page: 1 }))}
                        value={filters.maKhoa}
                        options={departments.map((d) => ({ label: `${d.MaKhoa} - ${d.TenKhoa}`, value: d.MaKhoa }))}
                      />
                    </Col>
                    <Col xs={12} sm={6} md={4}>
                      <Select
                        placeholder="Trạng thái"
                        allowClear
                        style={{ width: '100%' }}
                        onChange={(v) => setFilters((f) => ({ ...f, trangThai: v || undefined, page: 1 }))}
                        value={filters.trangThai}
                        options={STATUS_OPTIONS}
                      />
                    </Col>
                    <Col xs={12} sm={6} md={3}>
                      <Button onClick={handleClearFilters} block>Xóa lọc</Button>
                    </Col>
                  </Row>
                </Card>

                {/* ── Table */}
                <Card className={styles.tableCard}>
                  {isError ? (
                    <Empty description={<Text type="danger">Không thể tải danh sách giảng viên</Text>} />
                  ) : (
                    <Table
                      dataSource={teachers}
                      columns={columns}
                      rowKey="MaGV"
                      loading={isLoading}
                      scroll={{ x: 1100 }}
                      pagination={{
                        current: filters.page,
                        pageSize: filters.pageSize,
                        total,
                        showSizeChanger: true,
                        showTotal: (t) => `Tổng ${t} giảng viên`,
                        onChange: handlePageChange,
                      }}
                    />
                  )}
                </Card>
              </>
            ),
          },
        ]}
      />

      {/* ── Create / Edit Modal */}
      <Modal
        title={editRecord ? `Sửa giảng viên — ${editRecord.MaGV}` : 'Thêm giảng viên mới'}
        open={modalOpen}
        onCancel={handleCloseModal}
        footer={null}
        width={640}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item
                name="MaGV"
                label="Mã giảng viên"
                tooltip="Để trống để hệ thống tự sinh mã"
              >
                <Input
                  placeholder="VD: GV001 (bỏ trống để tự sinh)"
                  maxLength={20}
                  disabled={!!editRecord}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="TrangThai" label="Trạng thái">
                <Select options={STATUS_OPTIONS} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="Ho" label="Họ" rules={[{ required: true, message: 'Vui lòng nhập họ' }]}>
                <Input placeholder="VD: Nguyễn" maxLength={50} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="Ten" label="Tên" rules={[{ required: true, message: 'Vui lòng nhập tên' }]}>
                <Input placeholder="VD: Văn A" maxLength={50} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="email" label="Email" rules={[{ type: 'email', message: 'Email không hợp lệ' }]}>
                <Input placeholder="VD: nguyenvana@ptit.edu.vn" maxLength={100} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="SDT" label="Số điện thoại">
                <Input placeholder="VD: 0912345678" maxLength={20} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="NgaySinh" label="Ngày sinh">
                <Input type="date" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="GioiTinh" label="Giới tính">
                <Select placeholder="Chọn giới tính" allowClear options={GENDER_OPTIONS} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="MaCoSo" label="Cơ sở" rules={[{ required: true, message: 'Vui lòng chọn cơ sở' }]}>
                <Select
                  placeholder="Chọn cơ sở"
                  options={branches.map((b) => ({ label: b.TenCoSo, value: b.MaCoSo }))}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="MaKhoa" label="Khoa">
                <Select
                  placeholder="Chọn khoa"
                  allowClear
                  showSearch
                  optionFilterProp="children"
                  options={departments.map((d) => ({ label: `${d.MaKhoa} - ${d.TenKhoa}`, value: d.MaKhoa }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="HocVi" label="Học vị">
                <Select placeholder="Chọn học vị" allowClear options={DEGREE_OPTIONS} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="HocHam" label="Học hàm">
                <Input placeholder="VD: GTV, PGS" maxLength={50} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="DiaChi" label="Địa chỉ">
            <Input.TextArea placeholder="VD: Hà Nội, Việt Nam" rows={2} maxLength={300} showCount />
          </Form.Item>

          <Form.Item name="NgayVaoLam" label="Ngày vào làm">
            <Input type="date" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={handleCloseModal}>Hủy</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {editRecord ? 'Cập nhật' : 'Tạo mới'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* ── Detail Drawer */}
      <Drawer
        title={detailRecord ? `Chi tiết: ${detailRecord.MaGV}` : 'Chi tiết giảng viên'}
        placement="right"
        width={480}
        onClose={() => { setDrawerOpen(false); setDetailRecord(null); }}
        open={drawerOpen}
        extra={
          detailRecord && (
            <Space>
              <Button size="small" icon={<SwapOutlined />} onClick={() => { setDrawerOpen(false); handleOpenEdit(detailRecord); }}>
                Đổi trạng thái
              </Button>
              <Button size="small" type="primary" icon={<EditOutlined />} onClick={() => { setDrawerOpen(false); handleOpenEdit(detailRecord); }}>
                Sửa
              </Button>
            </Space>
          )
        }
      >
        {renderDrawer()}
      </Drawer>

    </div>
  );
}
