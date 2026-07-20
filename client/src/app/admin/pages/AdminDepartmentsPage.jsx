/**
 * Admin Departments Page - CRUD for departments
 */

import { useState } from 'react';
import {
  Card, Table, Button, Space, Tag, Typography, Modal, Form, Input,
  message, Popconfirm, Switch, Empty
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { departmentApi } from '@/services/admin/departmentApi';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './AdminPage.module.scss';

const { Title, Text } = Typography;

export default function AdminDepartmentsPage() {
  const [form] = Form.useForm();
  const [editRecord, setEditRecord] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: departments = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-departments'],
    queryFn: departmentApi.getAll,
  });

  const createMutation = useMutation({
    mutationFn: departmentApi.create,
    onSuccess: () => {
      message.success('Tạo khoa thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-departments'] });
      handleCloseModal();
    },
    onError: (err) => {
      const msg = getApiErrorMessage(err, 'Tạo khoa thất bại. Vui lòng thử lại.');
      message.error(msg);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ MaKhoa, data }) => departmentApi.update(MaKhoa, data),
    onSuccess: () => {
      message.success('Cập nhật khoa thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-departments'] });
      handleCloseModal();
    },
    onError: (err) => {
      const msg = getApiErrorMessage(err, 'Cập nhật khoa thất bại. Vui lòng thử lại.');
      message.error(msg);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: departmentApi.delete,
    onSuccess: () => {
      message.success('Xóa khoa thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-departments'] });
    },
    onError: (err) => {
      const msg = getApiErrorMessage(err, 'Xóa khoa thất bại. Vui lòng thử lại.');
      message.error(msg);
    },
  });

  const handleOpenCreate = () => {
    setEditRecord(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleOpenEdit = (record) => {
    setEditRecord(record);
    form.setFieldsValue({
      MaKhoa: record.MaKhoa,
      TenKhoa: record.TenKhoa,
      MoTa: record.MoTa,
      NgayThanhLap: record.NgayThanhLap || '',
      TrangThai: record.TrangThai === 'HoatDong',
    });
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setEditRecord(null);
    setModalOpen(false);
    form.resetFields();
  };

  const handleSubmit = (values) => {
    const payload = {
      TenKhoa: values.TenKhoa,
      MoTa: values.MoTa || null,
      NgayThanhLap: values.NgayThanhLap || null,
      TrangThai: values.TrangThai ? 'HoatDong' : 'NgungHoatDong',
    };
    if (editRecord) {
      updateMutation.mutate({ MaKhoa: editRecord.MaKhoa, data: payload });
    } else {
      createMutation.mutate({ ...payload, MaKhoa: values.MaKhoa });
    }
  };

  const columns = [
    {
      title: 'Mã khoa',
      dataIndex: 'MaKhoa',
      key: 'MaKhoa',
      width: 130,
      render: (code) => <Text strong code>{code}</Text>,
    },
    {
      title: 'Tên khoa',
      dataIndex: 'TenKhoa',
      key: 'TenKhoa',
    },
    {
      title: 'Mô tả',
      dataIndex: 'MoTa',
      key: 'MoTa',
      ellipsis: true,
      render: (v) => v || '—',
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThai',
      key: 'TrangThai',
      width: 160,
      render: (s) => (
        <Tag color={s === 'HoatDong' ? 'success' : 'error'}>
          {s === 'HoatDong' ? 'Hoạt động' : 'Ngừng hoạt động'}
        </Tag>
      ),
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 130,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleOpenEdit(record)}
            title="Sửa"
          />
          <Popconfirm
            title="Xác nhận xóa khoa này?"
            description="Hành động này không thể hoàn tác."
            onConfirm={() => deleteMutation.mutate(record.MaKhoa)}
            okText="Xóa"
            cancelText="Hủy"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              title="Xóa"
              loading={deleteMutation.isPending}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <Title level={3} className={styles.pageTitle}>Quản lý Khoa</Title>
          <Text type="secondary">Tạo mới và quản lý các khoa trong hệ thống</Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
            Thêm khoa
          </Button>
        </Space>
      </div>

      <Card className={styles.tableCard}>
        {isError ? (
          <Empty description={<Text type="danger">Không thể tải danh sách khoa</Text>} />
        ) : departments.length === 0 && !isLoading ? (
          <Empty description={<Text type="secondary">Chưa có khoa nào. Nhấn "Thêm khoa" để tạo mới.</Text>} />
        ) : (
          <Table
            dataSource={departments}
            columns={columns}
            rowKey="MaKhoa"
            loading={isLoading}
            pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t) => `Tổng ${t} khoa` }}
            scroll={{ x: 700 }}
          />
        )}
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        title={editRecord ? 'Sửa khoa' : 'Thêm khoa mới'}
        open={modalOpen}
        onCancel={handleCloseModal}
        footer={null}
        width={520}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ TrangThai: true }}
        >
          <Form.Item
            name="MaKhoa"
            label="Mã khoa"
            rules={[{ required: true, message: 'Vui lòng nhập mã khoa' }]}
          >
            <Input type="text" placeholder="VD: CNTT" maxLength={20}  value={editRecord?.MaKhoa} />
          </Form.Item>
          <Form.Item
            name="TenKhoa"
            label="Tên khoa"
            rules={[{ required: true, message: 'Vui lòng nhập tên khoa' }]}
          >
            <Input placeholder="VD: Công nghệ thông tin" maxLength={100} />
          </Form.Item>
          <Form.Item name="MoTa" label="Mô tả">
            <Input.TextArea placeholder="Mô tả về khoa (không bắt buộc)" rows={3} maxLength={500} showCount />
          </Form.Item>
          <Form.Item name="NgayThanhLap" label="Ngày thành lập">
            <Input placeholder="VD: 2020-01-15" maxLength={10} />
          </Form.Item>
          <Form.Item name="TrangThai" label="Trạng thái" valuePropName="checked">
            <Switch checkedChildren="Hoạt động" unCheckedChildren="Ngừng hoạt động" />
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
    </div>
  );
}
