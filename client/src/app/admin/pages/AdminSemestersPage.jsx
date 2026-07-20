/**
 * Admin Semesters Page - CRUD for semesters
 */

import { useState } from 'react';
import {
  Card, Table, Button, Space, Tag, Typography, Modal, Form, Input, Popconfirm,
  message, Drawer, Descriptions, Empty,
  Select, Tabs
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, ReloadOutlined,
  BarChartOutlined, UnorderedListOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { semesterApi } from '@/services/admin/semesterApi';
import { formatDate } from '@/utils/formatters';
import EntityOverviewDashboard from '../components/EntityOverviewDashboard';
import { useAdminEntityOverview } from '@/hooks/useAdminOverview';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './AdminPage.module.scss';

const { Title, Text } = Typography;

const SEMESTER_STATUS_OPTIONS = [
  { label: 'Sắp mở', value: 'SapMo' },
  { label: 'Đang đăng ký', value: 'DangDangKy' },
  { label: 'Đang học', value: 'DangHoc' },
  { label: 'Đã kết thúc', value: 'DaKetThuc' },
];

export default function AdminSemestersPage() {
  const [form] = Form.useForm();
  const [editRecord, setEditRecord] = useState(null);
  const [detailRecord, setDetailRecord] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const queryClient = useQueryClient();

  // ── Overview query
  const { data: overviewData, isLoading: isOverviewLoading, isError: isOverviewError, refetch: refetchOverview } =
    useAdminEntityOverview('semesters');

  const { data: semesterData, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-semesters'],
    queryFn: semesterApi.getAll,
  });

  // Backend returns: { items: Semester[], total: int }
  const semesters = semesterData?.items || semesterData || [];

  const createMutation = useMutation({
    mutationFn: semesterApi.create,
    onSuccess: () => {
      message.success('Tạo học kỳ thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-semesters'] });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Tạo học kỳ thất bại. Vui lòng thử lại.')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ MaHocKy, data }) => semesterApi.update(MaHocKy, data),
    onSuccess: () => {
      message.success('Cập nhật thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-semesters'] });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Cập nhật học kỳ thất bại. Vui lòng thử lại.')),
  });

  const deleteMutation = useMutation({
    mutationFn: semesterApi.delete,
    onSuccess: () => {
      message.success('Xóa học kỳ thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-semesters'] });
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Xóa học kỳ thất bại. Vui lòng thử lại.')),
  });

  const handleOpenEdit = (record) => {
    setEditRecord(record);
    form.setFieldsValue(record);
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
      updateMutation.mutate({ MaHocKy: editRecord.MaHocKy, data: values });
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
      SapMo: { color: 'default', label: 'Sắp mở' },
      DangDangKy: { color: 'processing', label: 'Đang đăng ký' },
      DangHoc: { color: 'success', label: 'Đang học' },
      DaKetThuc: { color: 'error', label: 'Đã kết thúc' },
    };
    return map[status] || { color: 'default', label: status || '—' };
  };

  const columns = [
    {
      title: 'Mã HK',
      dataIndex: 'MaHocKy',
      key: 'MaHocKy',
      width: 110,
      render: (code) => <Text strong code>{code}</Text>,
    },
    {
      title: 'Học kỳ',
      dataIndex: 'KySo',
      key: 'KySo',
      width: 90,
      align: 'center',
      render: (v) => v ? `HK${v}` : '—',
    },
    {
      title: 'Năm học',
      dataIndex: 'NamHoc',
      key: 'NamHoc',
      width: 120,
    },
    {
      title: 'Ngày bắt đầu',
      dataIndex: 'NgayBatDau',
      key: 'NgayBatDau',
      width: 130,
      render: (d) => formatDate(d),
    },
    {
      title: 'Ngày kết thúc',
      dataIndex: 'NgayKetThuc',
      key: 'NgayKetThuc',
      width: 130,
      render: (d) => formatDate(d),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThaiHocKy',
      key: 'TrangThaiHocKy',
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
            title="Xác nhận xóa học kỳ này?"
            description="Hành động này sẽ thất bại nếu học kỳ đang được sử dụng."
            onConfirm={() => deleteMutation.mutate(record.MaHocKy)}
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
                entity="semesters"
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
                    <Title level={3} className={styles.pageTitle}>Quản lý Học kỳ</Title>
                    <Text type="secondary">Danh sách và quản lý các học kỳ trong hệ thống</Text>
                  </div>
                  <Space>
                    <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
                      Thêm học kỳ
                    </Button>
                  </Space>
                </div>

                <Card className={styles.tableCard}>
                  {isError ? (
                    <Empty description={<Text type="danger">Không thể tải danh sách học kỳ</Text>} />
                  ) : (
                    <Table
                      dataSource={semesters}
                      columns={columns}
                      rowKey="MaHocKy"
                      loading={isLoading}
                      pagination={{ pageSize: 10, showTotal: (t) => `Tổng ${t} học kỳ` }}
                    />
                  )}
                </Card>
              </>
            ),
          },
        ]}
      />

      <Modal
        title={editRecord ? 'Sửa học kỳ' : 'Thêm học kỳ mới'}
        open={modalOpen}
        onCancel={handleCloseModal}
        footer={null}
        width={480}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="MaHocKy" label="Mã học kỳ" rules={[{ required: true, message: 'Vui lòng nhập mã HK' }]}>
            <Input placeholder="VD: HK20241" disabled={!!editRecord} maxLength={20} />
          </Form.Item>
          <Form.Item name="KySo" label="Kỳ số" rules={[{ required: true, message: 'Vui lòng nhập kỳ số' }]}>
            <Input type="number" placeholder="VD: 1" min={1} max={4} />
          </Form.Item>
          <Form.Item name="NamHoc" label="Năm học" rules={[{ required: true, message: 'Vui lòng nhập năm học' }]}>
            <Input placeholder="VD: 2024-2025" maxLength={20} />
          </Form.Item>
          <Form.Item name="NgayBatDau" label="Ngày bắt đầu">
            <Input type="date" />
          </Form.Item>
          <Form.Item name="NgayKetThuc" label="Ngày kết thúc">
            <Input type="date" />
          </Form.Item>
          <Form.Item name="TrangThaiHocKy" label="Trạng thái">
            <Select placeholder="Chọn trạng thái">
              {SEMESTER_STATUS_OPTIONS.map((o) => (
                <Select.Option key={o.value} value={o.value}>{o.label}</Select.Option>
              ))}
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
        title="Chi tiết học kỳ"
        placement="right"
        width={420}
        onClose={() => { setDrawerOpen(false); setDetailRecord(null); }}
        open={drawerOpen}
      >
        {detailRecord && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Mã HK"><Text strong code>{detailRecord.MaHocKy}</Text></Descriptions.Item>
            <Descriptions.Item label="Kỳ số">{detailRecord.KySo ? `HK${detailRecord.KySo}` : '—'}</Descriptions.Item>
            <Descriptions.Item label="Năm học">{detailRecord.NamHoc || '—'}</Descriptions.Item>
            <Descriptions.Item label="Ngày bắt đầu">{formatDate(detailRecord.NgayBatDau) || '—'}</Descriptions.Item>
            <Descriptions.Item label="Ngày kết thúc">{formatDate(detailRecord.NgayKetThuc) || '—'}</Descriptions.Item>
            <Descriptions.Item label="Trạng thái">
              {(() => { const p = getStatusProps(detailRecord.TrangThaiHocKy); return <Tag color={p.color}>{p.label}</Tag>; })()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
}
