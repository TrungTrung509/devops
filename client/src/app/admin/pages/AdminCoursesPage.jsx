/**
 * Admin Courses Page - CRUD for courses
 */

import { useState } from 'react';
import {
  Card, Table, Button, Space, Tag, Typography, Modal, Form, Input, Select, Popconfirm,
  message, Drawer, Descriptions, Empty, Tabs, Row, Col
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, ReloadOutlined,
  BarChartOutlined, UnorderedListOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { courseApi } from '@/services/admin/courseApi';
import { departmentApi, departmentKeys } from '@/services/admin/departmentApi';
import EntityOverviewDashboard from '../components/EntityOverviewDashboard';
import { useAdminEntityOverview } from '@/hooks/useAdminOverview';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './AdminPage.module.scss';

const { Title, Text } = Typography;

const TYPE_OPTIONS = [
  { label: 'Bắt buộc', value: 'BatBuoc' },
  { label: 'Tự chọn', value: 'TuChon' },
];

export default function AdminCoursesPage() {
  const [form] = Form.useForm();
  const [editRecord, setEditRecord] = useState(null);
  const [detailRecord, setDetailRecord] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [filters, setFilters] = useState({ keyword: '' });
  const [activeTab, setActiveTab] = useState('overview');
  const queryClient = useQueryClient();

  // ── Query: Departments (for dropdown)
  const { data: deptData } = useQuery({
    queryKey: departmentKeys.list(),
    queryFn: departmentApi.getAll,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
  const departments = Array.isArray(deptData) ? deptData : [];

  // ── Overview query
  const { data: overviewData, isLoading: isOverviewLoading, isError: isOverviewError, refetch: refetchOverview } =
    useAdminEntityOverview('courses');

  const { data: courseData, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-courses', filters],
    queryFn: () => courseApi.getAll(filters),
  });

  // Backend returns: { items: Course[], total: int }
  const courses = courseData?.items || courseData || [];

  const createMutation = useMutation({
    mutationFn: courseApi.create,
    onSuccess: () => {
      message.success('Tạo học phần thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-courses'] });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Tạo học phần thất bại. Vui lòng thử lại.')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ MaHocPhan, data }) => courseApi.update(MaHocPhan, data),
    onSuccess: () => {
      message.success('Cập nhật thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-courses'] });
      handleCloseModal();
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Cập nhật học phần thất bại. Vui lòng thử lại.')),
  });

  const deleteMutation = useMutation({
    mutationFn: courseApi.delete,
    onSuccess: () => {
      message.success('Xóa học phần thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-courses'] });
    },
    onError: (err) => message.error(getApiErrorMessage(err, 'Xóa học phần thất bại. Vui lòng thử lại.')),
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
      updateMutation.mutate({ MaHocPhan: editRecord.MaHocPhan, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDetail = (record) => {
    setDetailRecord(record);
    setDrawerOpen(true);
  };

  const columns = [
    {
      title: 'Mã HP',
      dataIndex: 'MaHocPhan',
      key: 'MaHocPhan',
      width: 110,
      render: (code) => <Text strong code>{code}</Text>,
    },
    {
      title: 'Tên học phần',
      dataIndex: 'TenHocPhan',
      key: 'TenHocPhan',
      ellipsis: true,
    },
    {
      title: 'Khoa',
      dataIndex: 'MaKhoa',
      key: 'MaKhoa',
      width: 120,
      render: (v) => {
        const d = departments.find((d) => d.MaKhoa === v);
        return <Text type="secondary">{d ? `${d.MaKhoa} - ${d.TenKhoa}` : v || '—'}</Text>;
      },
    },
    {
      title: 'Số TC',
      dataIndex: 'SoTinChi',
      key: 'SoTinChi',
      width: 80,
      align: 'center',
      render: (v) => <Tag>{v || '—'}</Tag>,
    },
    {
      title: 'Loại',
      dataIndex: 'LoaiHocPhan',
      key: 'LoaiHocPhan',
      width: 110,
      render: (v) => {
        const map = { BatBuoc: 'Bắt buộc', TuChon: 'Tự chọn' };
        return <Tag color={v === 'BatBuoc' ? 'blue' : 'green'}>{map[v] || v || '—'}</Tag>;
      },
    },
    {
      title: 'Mô tả',
      dataIndex: 'MoTa',
      key: 'MoTa',
      ellipsis: true,
      render: (v) => v || '—',
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
          <Popconfirm title="Xác nhận xóa học phần?" onConfirm={() => deleteMutation.mutate(record.MaHocPhan)} okText="Xóa" cancelText="Hủy" okButtonProps={{ danger: true }}>
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
                entity="courses"
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
                    <Title level={3} className={styles.pageTitle}>Quản lý Học phần</Title>
                    <Text type="secondary">Danh sách và quản lý các học phần trong hệ thống</Text>
                  </div>
                  <Space>
                    <Input.Search
                      placeholder="Tìm theo mã, tên..."
                      onSearch={(val) => setFilters((f) => ({ ...f, keyword: val }))}
                      style={{ width: 200 }}
                      allowClear
                    />
                    <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
                      Thêm học phần
                    </Button>
                  </Space>
                </div>

                <Card className={styles.tableCard}>
                  {isError ? (
                    <Empty description={<Text type="danger">Không thể tải danh sách học phần</Text>} />
                  ) : (
                    <Table
                      dataSource={courses}
                      columns={columns}
                      rowKey="MaHocPhan"
                      loading={isLoading}
                      pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t) => `Tổng ${t} học phần` }}
                      scroll={{ x: 800 }}
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
        title={editRecord ? 'Sửa học phần' : 'Thêm học phần mới'}
        open={modalOpen}
        onCancel={handleCloseModal}
        footer={null}
        width={520}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="MaHocPhan" label="Mã học phần" rules={[{ required: true, message: 'Vui lòng nhập mã HP' }]}>
            <Input placeholder="VD: CS101" disabled={!!editRecord} maxLength={20} />
          </Form.Item>
          <Form.Item name="TenHocPhan" label="Tên học phần" rules={[{ required: true, message: 'Vui lòng nhập tên' }]}>
            <Input placeholder="VD: Nhập môn Công nghệ phần mềm" maxLength={200} />
          </Form.Item>
          <Form.Item name="MaKhoa" label="Khoa" rules={[{ required: true, message: 'Vui lòng chọn khoa' }]}>
            <Select placeholder="Chọn khoa" allowClear showSearch optionFilterProp="children" options={departments.map((d) => ({ label: `${d.MaKhoa} - ${d.TenKhoa}`, value: d.MaKhoa }))} />
          </Form.Item>
          <Form.Item name="SoTinChi" label="Số tín chỉ" rules={[{ required: true, message: 'Vui lòng nhập số tín chỉ' }]}>
            <Input type="number" placeholder="VD: 3" min={1} max={10} />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="SoTietLyThuyet" label="Số tiết lý thuyết" rules={[{ required: true, message: 'Nhập số tiết LT' }]}>
                <Input type="number" placeholder="VD: 30" min={0} max={120} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="SoTietThucHanh" label="Số tiết thực hành" rules={[{ required: true, message: 'Nhập số tiết TH' }]}>
                <Input type="number" placeholder="VD: 15" min={0} max={120} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="LoaiHocPhan" label="Loại học phần">
            <Select placeholder="Chọn loại" allowClear>
              {TYPE_OPTIONS.map((o) => <Select.Option key={o.value} value={o.value}>{o.label}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="MoTa" label="Mô tả">
            <Input.TextArea placeholder="Mô tả học phần..." rows={3} maxLength={500} showCount />
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
        title="Chi tiết học phần"
        placement="right"
        width={420}
        onClose={() => { setDrawerOpen(false); setDetailRecord(null); }}
        open={drawerOpen}
      >
        {detailRecord && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Mã HP"><Text strong code>{detailRecord.MaHocPhan}</Text></Descriptions.Item>
            <Descriptions.Item label="Tên học phần">{detailRecord.TenHocPhan}</Descriptions.Item>
            <Descriptions.Item label="Khoa">
              {(() => {
                const d = departments.find((d) => d.MaKhoa === detailRecord.MaKhoa);
                return d ? `${d.MaKhoa} - ${d.TenKhoa}` : detailRecord.MaKhoa || '—';
              })()}
            </Descriptions.Item>
            <Descriptions.Item label="Số tín chỉ">{detailRecord.SoTinChi || '—'}</Descriptions.Item>
            <Descriptions.Item label="Số tiết lý thuyết">{detailRecord.SoTietLyThuyet ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Số tiết thực hành">{detailRecord.SoTietThucHanh ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Loại">
              {detailRecord.LoaiHocPhan ? (
                <Tag color={detailRecord.LoaiHocPhan === 'BatBuoc' ? 'blue' : 'green'}>
                  {detailRecord.LoaiHocPhan === 'BatBuoc' ? 'Bắt buộc' : 'Tự chọn'}
                </Tag>
              ) : '—'}
            </Descriptions.Item>
            <Descriptions.Item label="Mô tả">{detailRecord.MoTa || '—'}</Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
}
