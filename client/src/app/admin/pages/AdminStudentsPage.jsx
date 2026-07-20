/**
 * Admin Students Page - Full CRUD for students
 * Backend: GET /students/ (list paginated), GET /students/{maSV}, POST /students/, PUT /students/{maSV},
 *         PATCH /students/{maSV}/status, DELETE /students/{maSV}
 *
 * Student fields (PascalCase from backend):
 *   MaSV, Ho, Ten, email(lowercase in schema), SDT, NgaySinh, GioiTinh, DiaChi,
 *   MaCoSo, MaKhoa, TrangThai, NgayNhapHoc, NgayTao, userId
 *
 * StudentStatus enum: DangHoc | BaoLuu | ThoiHoc | TotNghiep
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
import { studentApi, studentKeys } from '@/services/admin/studentApi';
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
  DangHoc:   { color: 'success', label: 'Đang học' },
  BaoLuu:    { color: 'warning', label: 'Bảo lưu' },
  ThoiHoc:   { color: 'error',   label: 'Thôi học' },
  TotNghiep: { color: 'blue',     label: 'Tốt nghiệp' },
};

const GENDER_MAP = {
  Nam:  'Nam',
  Nu:   'Nữ',
  Khac: 'Khác',
};

const STATUS_OPTIONS = [
  { label: 'Đang học',  value: 'DangHoc'   },
  { label: 'Bảo lưu',   value: 'BaoLuu'    },
  { label: 'Thôi học',  value: 'ThoiHoc'   },
  { label: 'Tốt nghiệp', value: 'TotNghiep' },
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

function toISODateString(value) {
  if (!value) return undefined;
  if (typeof value === 'string') return value.slice(0, 10);
  if (typeof value.format === 'function') return value.format('YYYY-MM-DD');
  return String(value);
}

// ─── Component ─────────────────────────────────────────────────────────────

export default function AdminStudentsPage() {
  const queryClient = useQueryClient();
  const [form] = Form.useForm();

  // ── Tab state
  const [activeTab, setActiveTab] = useState('overview');

  // ── Overview query
  const { data: overviewData, isLoading: isOverviewLoading, isError: isOverviewError, refetch: refetchOverview } =
    useAdminEntityOverview('students');

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
  const [drawerOpen, setDrawerOpen]  = useState(false);
  const [editRecord, setEditRecord]  = useState(null);
  const [detailRecord, setDetailRecord] = useState(null);

  // ── Query: Students (paginated, filters in camelCase for API)
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: studentKeys.list(filters),
    queryFn: () => studentApi.getAll(filters),
    select: (res) => ({
      items: res.items || [],
      total: res.total || 0,
      stats: res.stats || {},
    }),
    keepPreviousData: true,
  });

  const students = data?.items || [];
  const total     = data?.total || 0;

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
    mutationFn: studentApi.create,
    onSuccess: () => {
      message.success('Thêm sinh viên thành công!');
      queryClient.invalidateQueries({ queryKey: studentKeys.all });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Thêm sinh viên thất bại. Vui lòng thử lại.')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ MaSV, data: payload }) => studentApi.update(MaSV, payload),
    onSuccess: () => {
      message.success('Cập nhật thành công!');
      queryClient.invalidateQueries({ queryKey: studentKeys.all });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Cập nhật sinh viên thất bại. Vui lòng thử lại.')),
  });

  const statusMutation = useMutation({
    mutationFn: ({ MaSV, TrangThai }) => studentApi.updateStatus(MaSV, TrangThai),
    onSuccess: () => {
      message.success('Đổi trạng thái thành công!');
      queryClient.invalidateQueries({ queryKey: studentKeys.all });
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Đổi trạng thái sinh viên thất bại. Vui lòng thử lại.')),
  });

  const deleteMutation = useMutation({
    mutationFn: studentApi.delete,
    onSuccess: () => {
      message.success('Xóa sinh viên thành công!');
      queryClient.invalidateQueries({ queryKey: studentKeys.all });
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Xóa sinh viên thất bại. Vui lòng thử lại.')),
  });

  // ── Handlers
  const handleOpenCreate = () => {
    setEditRecord(null);
    form.resetFields();
    form.setFieldsValue({ TrangThai: 'DangHoc' });
    setModalOpen(true);
  };

  const handleOpenEdit = (record) => {
    setEditRecord(record);
    form.setFieldsValue({
      MaSV:       record.MaSV,
      Ho:         record.Ho,
      Ten:        record.Ten,
      email:      record.email ?? record.Email ?? '',
      SDT:        record.SDT,
      NgaySinh:   record.NgaySinh,
      GioiTinh:   record.GioiTinh,
      DiaChi:     record.DiaChi,
      MaCoSo:     record.MaCoSo,
      MaKhoa:     record.MaKhoa,
      TrangThai:  record.TrangThai,
      NgayNhapHoc: record.NgayNhapHoc,
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
      NgaySinh:    toISODateString(values.NgaySinh),
      NgayNhapHoc: toISODateString(values.NgayNhapHoc),
    };

    if (editRecord) {
      updateMutation.mutate({ MaSV: editRecord.MaSV, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleDetail = (record) => {
    setDetailRecord(record);
    setDrawerOpen(true);
  };

  const handleChangeStatus = (MaSV, newStatus) => {
    if (newStatus === 'ThoiHoc') {
      Modal.confirm({
        title: 'Xác nhận đổi trạng thái',
        content: 'Chuyển sinh viên sang "Thôi học"? Hành động này sẽ cập nhật trạng thái sinh viên.',
        okText: 'Xác nhận',
        cancelText: 'Hủy',
        onOk: () => statusMutation.mutate({ MaSV, TrangThai: newStatus }),
      });
    } else {
      statusMutation.mutate({ MaSV, TrangThai: newStatus });
    }
  };

  const handleClearFilters = () => {
    setFilters({ keyword: undefined, maCoSo: 'HADONG', maKhoa: undefined, trangThai: undefined, page: 1, pageSize: 10 });
  };

  const handlePageChange = (page, pageSize) => {
    setFilters((f) => ({ ...f, page, pageSize: pageSize ?? f.pageSize }));
  };

  // ── Statistics from data (Backend returns stats: { DangHoc, BaoLuu, ThoiHoc, TotNghiep })
  const stats = {
    total:     total,
    active:    data?.stats?.DangHoc ?? 0,
    reserved:  data?.stats?.BaoLuu ?? 0,
    dropped:   data?.stats?.ThoiHoc ?? 0,
    graduated: data?.stats?.TotNghiep ?? 0,
  };

  // ── Table columns
  const columns = [
    {
      title: 'Mã SV',
      dataIndex: 'MaSV',
      key: 'MaSV',
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
      title: 'Ngày sinh',
      dataIndex: 'NgaySinh',
      key: 'NgaySinh',
      width: 110,
      render: (v) => <Text type="secondary" style={{ fontSize: 12 }}>{formatDate(v)}</Text>,
    },
    {
      title: 'Giới tính',
      dataIndex: 'GioiTinh',
      key: 'GioiTinh',
      width: 90,
      render: (v) => getGenderLabel(v),
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
            onChange={(val) => handleChangeStatus(record.MaSV, val)}
            options={STATUS_OPTIONS}
            variant="borderless"
          /> */}
          <Popconfirm
            title="Xác nhận xóa sinh viên này?"
            description="Hành động không thể hoàn tác."
            onConfirm={() => deleteMutation.mutate(record.MaSV)}
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
        <Descriptions.Item label="Mã SV">
          <Text strong code>{r.MaSV}</Text>
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
        <Descriptions.Item label="Trạng thái">
          <Tag color={sp.color}>{sp.label}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Ngày nhập học">{formatDate(r.NgayNhapHoc)}</Descriptions.Item>
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
                entity="students"
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
                    <Title level={3} className={styles.pageTitle}>Quản lý Sinh viên</Title>
                    <Text type="secondary">Thêm, sửa, xóa và quản lý thông tin sinh viên trong hệ thống</Text>
                  </div>
                  <Space>
                    <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
                      Thêm sinh viên
                    </Button>
                  </Space>
                </div>

                {/* ── Stats Row */}
                <Row gutter={[12, 12]}>
                  {[
                    { label: 'Tổng cộng',  value: total,          color: '#1677ff', icon: <TeamOutlined /> },
                    { label: 'Đang học',    value: stats.active,    color: '#52c41a', icon: <TeamOutlined /> },
                    { label: 'Bảo lưu',     value: stats.reserved,  color: '#faad14', icon: <TeamOutlined /> },
                    { label: 'Tốt nghiệp',  value: stats.graduated,  color: '#722ed1', icon: <TeamOutlined /> },
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
                        placeholder="Tìm mã SV, họ, tên..."
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
                    <Empty description={<Text type="danger">Không thể tải danh sách sinh viên</Text>} />
                  ) : (
                    <Table
                      dataSource={students}
                      columns={columns}
                      rowKey="MaSV"
                      loading={isLoading}
                      scroll={{ x: 1100 }}
                      pagination={{
                        current: filters.page,
                        pageSize: filters.pageSize,
                        total,
                        showSizeChanger: true,
                        showTotal: (t) => `Tổng ${t} sinh viên`,
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
        title={editRecord ? `Sửa sinh viên — ${editRecord.MaSV}` : 'Thêm sinh viên mới'}
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
                name="MaSV"
                label="Mã sinh viên"
                tooltip="Để trống để hệ thống tự sinh mã"
              >
                <Input
                  placeholder="VD: SV001 (bỏ trống để tự sinh)"
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
                <Input placeholder="VD: sv001@ptit.edu.vn" maxLength={100} />
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
              <Form.Item name="NgayNhapHoc" label="Ngày nhập học">
                <Input type="date" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="DiaChi" label="Địa chỉ">
            <Input.TextArea placeholder="VD: Hà Nội, Việt Nam" rows={2} maxLength={300} showCount />
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
        title={detailRecord ? `Chi tiết: ${detailRecord.MaSV}` : 'Chi tiết sinh viên'}
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
