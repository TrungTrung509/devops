/**
 * Admin Classrooms Page - CRUD for classrooms
 */

import { useState, useEffect, useRef } from 'react';
import {
  Card, Table, Button, Space, Tag, Typography, Modal, Form, Input, Select, Popconfirm,
  message, Drawer, Descriptions, Empty, Tabs
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, ReloadOutlined,
  BarChartOutlined, UnorderedListOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { classroomApi, classroomKeys } from '@/services/admin/classroomApi';
import { branchApi } from '@/services/admin/branchApi';
import EntityOverviewDashboard from '../components/EntityOverviewDashboard';
import { useAdminEntityOverview } from '@/hooks/useAdminOverview';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './AdminPage.module.scss';

const { Title, Text } = Typography;

const ROOM_TYPE_OPTIONS = [
  { label: 'Lý thuyết', value: 'LyThuyet' },
  { label: 'Thực hành', value: 'ThucHanh' },
  { label: 'Hội trường', value: 'HoiTruong' },
  { label: 'Phòng máy', value: 'MayTinh' },
  { label: 'Thí nghiệm', value: 'ThiNghiem' },
];

const ROOM_STATUS_OPTIONS = [
  { label: 'Hoạt động', value: 'HoatDong' },
  { label: 'Bảo trì', value: 'BaoTri' },
  { label: 'Ngừng sử dụng', value: 'NgungSuDung' },
];

export default function AdminClassroomsPage() {
  const [form] = Form.useForm();
  const [editRecord, setEditRecord] = useState(null);
  const [detailRecord, setDetailRecord] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [keywordInput, setKeywordInput] = useState('');
  const [filters, setFilters] = useState({
    keyword: undefined,
    maCoSo: undefined,
    loaiPhong: undefined,
    trangThai: undefined,
  });
  const [activeTab, setActiveTab] = useState('overview');
  const queryClient = useQueryClient();

  // ── Overview query
  const { data: overviewData, isLoading: isOverviewLoading, isError: isOverviewError, refetch: refetchOverview } =
    useAdminEntityOverview('classrooms');

  // Debounce keyword: 400ms sau khi gõ thì mới trigger API
  const debounceTimerRef = useRef(null);
  useEffect(() => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(() => {
      setFilters(prev => ({ ...prev, keyword: keywordInput || undefined }));
    }, 400);
    return () => { if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current); };
  }, [keywordInput]);

  const { data: classroomData, isLoading, isError, refetch } = useQuery({
    queryKey: classroomKeys.list(filters),
    queryFn: () => classroomApi.getAll(filters),
  });

  // Backend returns: { items: Classroom[], total: int }
  const classrooms = classroomData?.items || classroomData || [];
  const total = classroomData?.total ?? classrooms.length;

  const { data: branches = [] } = useQuery({
    queryKey: ['admin-branches-classroom'],
    queryFn: branchApi.getAll,
  });

  const createMutation = useMutation({
    mutationFn: classroomApi.create,
    onSuccess: () => {
      message.success('Tạo phòng học thành công!');
      queryClient.invalidateQueries({ queryKey: classroomKeys.all });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Tạo phòng học thất bại. Vui lòng thử lại.')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ MaPhong, data }) => classroomApi.update(MaPhong, data),
    onSuccess: () => {
      message.success('Cập nhật thành công!');
      queryClient.invalidateQueries({ queryKey: classroomKeys.all });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Cập nhật phòng học thất bại. Vui lòng thử lại.')),
  });

  const deleteMutation = useMutation({
    mutationFn: classroomApi.delete,
    onSuccess: () => {
      message.success('Xóa phòng học thành công!');
      queryClient.invalidateQueries({ queryKey: classroomKeys.all });
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Xóa phòng học thất bại. Vui lòng thử lại.')),
  });

  const handleOpenEdit = (record) => {
    setEditRecord(record);
    form.setFieldsValue({
      MaPhong: record.MaPhong,
      TenPhong: record.TenPhong,
      ToaNha: record.ToaNha,
      Tang: record.Tang,
      SucChua: record.SucChua,
      LoaiPhong: record.LoaiPhong,
      MaCoSo: record.MaCoSo,
      TrangThai: record.TrangThai,
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
      updateMutation.mutate({ MaPhong: editRecord.MaPhong, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDetail = (record) => {
    setDetailRecord(record);
    setDrawerOpen(true);
  };

  const getStatusProps = (status) => {
    const map = {
      HoatDong: { color: 'success', label: 'Hoạt động' },
      BaoTri: { color: 'warning', label: 'Bảo trì' },
      NgungSuDung: { color: 'error', label: 'Ngừng sử dụng' },
    };
    const p = map[status] || { color: 'default', label: status || '—' };
    return p;
  };

  const columns = [
    {
      title: 'Mã phòng',
      dataIndex: 'MaPhong',
      key: 'MaPhong',
      width: 110,
      render: (code) => <Text strong code>{code}</Text>,
    },
    {
      title: 'Tên phòng',
      dataIndex: 'TenPhong',
      key: 'TenPhong',
    },
    {
      title: 'Loại phòng',
      dataIndex: 'LoaiPhong',
      key: 'LoaiPhong',
      width: 120,
      render: (v) => {
        const map = {
          LyThuyet: 'Lý thuyết',
          ThucHanh: 'Thực hành',
          PhongMay: 'Phòng máy',
          MayTinh: 'Máy tính',
          HoiTruong: 'Hội trường',
          ThiNghiem: 'Thí nghiệm',
          Khac: 'Khác',
        };
        return <Tag>{map[v] || v || '—'}</Tag>;
      },
    },
    {
      title: 'Sức chứa',
      dataIndex: 'SucChua',
      key: 'SucChua',
      width: 100,
      align: 'center',
      render: (v) => v || '—',
    },
    {
      title: 'Cơ sở',
      dataIndex: 'MaCoSo',
      key: 'MaCoSo',
      width: 110,
      render: (v) => {
        const branch = branches.find((b) => b.MaCoSo === v);
        return <Tag color="blue">{branch?.TenCoSo || v || '—'}</Tag>;
      },
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
      title: 'Thao tác',
      key: 'actions',
      width: 140,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button type="text" icon={<EyeOutlined />} onClick={() => handleDetail(record)} />
          <Button type="text" icon={<EditOutlined />} onClick={() => handleOpenEdit(record)} />
          <Popconfirm
            title="Xác nhận xóa phòng học?"
            description="Hành động này sẽ thất bại nếu phòng đang được sử dụng trong lịch học."
            onConfirm={() => deleteMutation.mutate(record.MaPhong)}
            okText="Xóa" cancelText="Hủy" okButtonProps={{ danger: true }}
          >
            <Button type="text" danger icon={<DeleteOutlined />} loading={deleteMutation.isPending} />
          </Popconfirm>
        </Space>
      ),
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
                entity="classrooms"
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
                    <Title level={3} className={styles.pageTitle}>Quản lý Phòng học</Title>
                    <Text type="secondary">Danh sách và quản lý các phòng học trong hệ thống</Text>
                  </div>
                  <Space>
                    <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
                      Thêm phòng học
                    </Button>
                  </Space>
                </div>

                <Card className={styles.tableCard}>
                  <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                    <Input
                      placeholder="Tìm mã phòng, tên phòng..."
                      allowClear
                      style={{ width: 220 }}
                      value={keywordInput}
                      onChange={(e) => setKeywordInput(e.target.value)}
                    />
                    <Select
                      placeholder="Lọc cơ sở"
                      allowClear
                      style={{ width: 160 }}
                      onChange={(value) => setFilters(prev => ({ ...prev, maCoSo: value || undefined }))}
                    >
                      {branches.map((b) => <Select.Option key={b.MaCoSo} value={b.MaCoSo}>{b.TenCoSo}</Select.Option>)}
                    </Select>
                    <Select
                      placeholder="Lọc loại phòng"
                      allowClear
                      style={{ width: 140 }}
                      onChange={(value) => setFilters(prev => ({ ...prev, loaiPhong: value || undefined }))}
                    >
                      {ROOM_TYPE_OPTIONS.map((o) => <Select.Option key={o.value} value={o.value}>{o.label}</Select.Option>)}
                    </Select>
                    <Select
                      placeholder="Lọc trạng thái"
                      allowClear
                      style={{ width: 160 }}
                      onChange={(value) => setFilters(prev => ({ ...prev, trangThai: value || undefined }))}
                    >
                      {ROOM_STATUS_OPTIONS.map((o) => <Select.Option key={o.value} value={o.value}>{o.label}</Select.Option>)}
                    </Select>
                  </div>
                  {isError ? (
                    <Empty description={<Text type="danger">Không thể tải danh sách phòng học</Text>} />
                  ) : (
                    <Table
                      dataSource={classrooms}
                      columns={columns}
                      rowKey="MaPhong"
                      loading={isLoading}
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showTotal: (t) => `Tổng ${t} phòng học`,
                      }}
                    />
                  )}
                </Card>
              </>
            ),
          },
        ]}
      />

      <Modal
        title={editRecord ? 'Sửa phòng học' : 'Thêm phòng học mới'}
        open={modalOpen}
        onCancel={handleCloseModal}
        footer={null}
        width={480}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="MaPhong" label="Mã phòng" rules={[{ required: true, message: 'Vui lòng nhập mã phòng' }]}>
            <Input placeholder="VD: A101" disabled={!!editRecord} maxLength={20} />
          </Form.Item>
          <Form.Item name="TenPhong" label="Tên phòng" rules={[{ required: true, message: 'Vui lòng nhập tên phòng' }]}>
            <Input placeholder="VD: Phòng A101" maxLength={100} />
          </Form.Item>
          <Form.Item name="ToaNha" label="Tòa nhà">
            <Input placeholder="VD: Tòa A" maxLength={50} />
          </Form.Item>
          <Form.Item name="Tang" label="Tầng">
            <Input type="number" placeholder="VD: 1" min={0} max={100} />
          </Form.Item>
          <Form.Item name="SucChua" label="Sức chứa" rules={[{ required: true, message: 'Vui lòng nhập sức chứa' }]}>
            <Input type="number" placeholder="VD: 50" min={1} max={1000} />
          </Form.Item>
          <Form.Item name="LoaiPhong" label="Loại phòng">
            <Select placeholder="Chọn loại phòng" allowClear>
              {ROOM_TYPE_OPTIONS.map((o) => <Select.Option key={o.value} value={o.value}>{o.label}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="MaCoSo" label="Cơ sở">
            <Select placeholder="Chọn cơ sở" allowClear>
              {branches.map((b) => <Select.Option key={b.MaCoSo} value={b.MaCoSo}>{b.TenCoSo}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="TrangThai" label="Trạng thái">
            <Select placeholder="Chọn trạng thái">
              {ROOM_STATUS_OPTIONS.map((o) => <Select.Option key={o.value} value={o.value}>{o.label}</Select.Option>)}
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

      <Drawer
        title="Chi tiết phòng học"
        placement="right"
        width={420}
        onClose={() => { setDrawerOpen(false); setDetailRecord(null); }}
        open={drawerOpen}
      >
        {detailRecord && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Mã phòng"><Text strong code>{detailRecord.MaPhong}</Text></Descriptions.Item>
            <Descriptions.Item label="Tên phòng">{detailRecord.TenPhong}</Descriptions.Item>
            <Descriptions.Item label="Tòa nhà">{detailRecord.ToaNha || '—'}</Descriptions.Item>
            <Descriptions.Item label="Tầng">{detailRecord.Tang ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Loại phòng">{(() => {
              const m = {
                LyThuyet: 'Lý thuyết',
                ThucHanh: 'Thực hành',
                PhongMay: 'Phòng máy',
                MayTinh: 'Máy tính',
                HoiTruong: 'Hội trường',
                ThiNghiem: 'Thí nghiệm',
                Khac: 'Khác',
              };
              return m[detailRecord.LoaiPhong] || detailRecord.LoaiPhong || '—';
            })()}</Descriptions.Item>
            <Descriptions.Item label="Sức chứa">{detailRecord.SucChua || '—'}</Descriptions.Item>
            <Descriptions.Item label="Cơ sở">{detailRecord.MaCoSo || '—'}</Descriptions.Item>
            <Descriptions.Item label="Trạng thái">
              {(() => { const p = getStatusProps(detailRecord.TrangThai); return <Tag color={p.color}>{p.label}</Tag>; })()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
}
