/**
 * Admin Branches Page - CRUD for branches/campuses
 */

import { useState } from 'react';
import {
  Card, Table, Button, Space, Tag, Typography, Modal, Form, Input, Popconfirm,
  message, Drawer, Descriptions, Empty, Switch
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, ReloadOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { branchApi } from '@/services/admin/branchApi';
import { formatDate } from '@/utils/formatters';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './AdminPage.module.scss';

const { Title, Text } = Typography;

export default function AdminBranchesPage() {
  const [form] = Form.useForm();
  const [editRecord, setEditRecord] = useState(null);
  const [detailRecord, setDetailRecord] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: branches = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-branches'],
    queryFn: branchApi.getAll,
  });

  const createMutation = useMutation({
    mutationFn: branchApi.create,
    onSuccess: () => {
      message.success('Tạo cơ sở thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-branches'] });
      handleCloseModal();
    },
    onError: (err) => {
      const msg = getApiErrorMessage(err, 'Tạo cơ sở thất bại. Vui lòng thử lại.');
      message.error(msg);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ MaCoSo, data }) => branchApi.update(MaCoSo, data),
    onSuccess: () => {
      message.success('Cập nhật cơ sở thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-branches'] });
      handleCloseModal();
    },
    onError: (err) => {
      const msg = getApiErrorMessage(err, 'Cập nhật cơ sở thất bại. Vui lòng thử lại.');
      message.error(msg);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: branchApi.delete,
    onSuccess: () => {
      message.success('Xóa cơ sở thành công!');
      queryClient.invalidateQueries({ queryKey: ['admin-branches'] });
    },
    onError: (err) => {
      const msg = getApiErrorMessage(err, 'Xóa cơ sở thất bại. Vui lòng thử lại.');
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
      MaCoSo: record.MaCoSo,
      TenCoSo: record.TenCoSo,
      DiaChi: record.DiaChi,
      SoDienThoai: record.SoDienThoai,
      Email: record.Email,
      TrangThai: record.TrangThai === 'HoatDong',
    });
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setEditRecord(null);
    setModalOpen(false);
    form.resetFields();
  };

  const handleSubmit = async (values) => {
    // Map form camelCase names to backend PascalCase
    const payload = {
      MaCoSo: values.MaCoSo,
      TenCoSo: values.TenCoSo,
      DiaChi: values.DiaChi,
      SoDienThoai: values.SoDienThoai,
      Email: values.Email,
      TrangThai: values.TrangThai ? 'HoatDong' : 'NgungHoatDong',
    };
    if (editRecord) {
      updateMutation.mutate({ MaCoSo: editRecord.MaCoSo, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleDetail = (record) => {
    setDetailRecord(record);
    setDrawerOpen(true);
  };

  const columns = [
    {
      title: 'Mã cơ sở',
      dataIndex: 'MaCoSo',
      key: 'MaCoSo',
      width: 120,
      render: (code) => <Text strong code>{code}</Text>,
    },
    {
      title: 'Tên cơ sở',
      dataIndex: 'TenCoSo',
      key: 'TenCoSo',
    },
    {
      title: 'Địa chỉ',
      dataIndex: 'DiaChi',
      key: 'DiaChi',
      ellipsis: true,
    },
    {
      title: 'SĐT',
      dataIndex: 'SoDienThoai',
      key: 'SoDienThoai',
      width: 130,
    },
    {
      title: 'Email',
      dataIndex: 'Email',
      key: 'Email',
      width: 180,
      ellipsis: true,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThai',
      key: 'TrangThai',
      width: 130,
      render: (status) => (
        <Tag color={status === 'HoatDong' ? 'success' : 'error'}>
          {status === 'HoatDong' ? 'Hoạt động' : 'Ngừng hoạt động'}
        </Tag>
      ),
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 160,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleDetail(record)}
            title="Chi tiết"
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleOpenEdit(record)}
            title="Sửa"
          />
          <Popconfirm
            title="Xác nhận xóa cơ sở này?"
            description="Hành động này không thể hoàn tác."
            onConfirm={() => deleteMutation.mutate(record.MaCoSo)}
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
          <Title level={3} className={styles.pageTitle}>Quản lý Cơ sở</Title>
          <Text type="secondary">Danh sách và quản lý các cơ sở đào tạo trong hệ thống</Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
            Thêm cơ sở
          </Button>
        </Space>
      </div>

      <Card className={styles.tableCard}>
        {isError ? (
          <Empty description={<Text type="danger">Không thể tải danh sách cơ sở</Text>} />
        ) : (
          <Table
            dataSource={branches}
            columns={columns}
            rowKey="MaCoSo"
            loading={isLoading}
            pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t) => `Tổng ${t} cơ sở` }}
            scroll={{ x: 900 }}
          />
        )}
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        title={editRecord ? 'Sửa cơ sở' : 'Thêm cơ sở mới'}
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
            name="MaCoSo"
            label="Mã cơ sở"
            rules={[{ required: true, message: 'Vui lòng nhập mã cơ sở' }]}
          >
            <Input placeholder="VD: HADONG" disabled={!!editRecord} maxLength={20} />
          </Form.Item>
          <Form.Item
            name="TenCoSo"
            label="Tên cơ sở"
            rules={[{ required: true, message: 'Vui lòng nhập tên cơ sở' }]}
          >
            <Input placeholder="VD: Cơ sở Hà Nội" maxLength={100} />
          </Form.Item>
          <Form.Item name="DiaChi" label="Địa chỉ">
            <Input placeholder="VD: Hà Nội, Việt Nam" maxLength={200} />
          </Form.Item>
          <Form.Item name="SoDienThoai" label="Số điện thoại">
            <Input placeholder="VD: 024-1234-5678" maxLength={20} />
          </Form.Item>
          <Form.Item name="Email" label="Email">
            <Input placeholder="VD: hadong@ptit.edu.vn" maxLength={100} />
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

      {/* Detail Drawer */}
      <Drawer
        title="Chi tiết cơ sở"
        placement="right"
        width={420}
        onClose={() => { setDrawerOpen(false); setDetailRecord(null); }}
        open={drawerOpen}
      >
        {detailRecord && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Mã cơ sở">
              <Text strong code>{detailRecord.MaCoSo}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Tên cơ sở">{detailRecord.TenCoSo}</Descriptions.Item>
            <Descriptions.Item label="Địa chỉ">{detailRecord.DiaChi || '—'}</Descriptions.Item>
            <Descriptions.Item label="Số điện thoại">{detailRecord.SoDienThoai || '—'}</Descriptions.Item>
            <Descriptions.Item label="Email">{detailRecord.Email || '—'}</Descriptions.Item>
            <Descriptions.Item label="Trạng thái">
              <Tag color={detailRecord.TrangThai === 'HoatDong' ? 'success' : 'error'}>
                {detailRecord.TrangThai === 'HoatDong' ? 'Hoạt động' : 'Ngừng hoạt động'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Ngày thành lập">
              {formatDate(detailRecord.NgayThanhLap) || '—'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
}
