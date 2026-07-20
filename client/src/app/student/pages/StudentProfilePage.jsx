/**
 * Student Profile Page - View and update student profile
 */

import { useState } from 'react';
import { Card, Row, Col, Typography, Descriptions, Tag, Button, Skeleton, Form, Input, message, Modal, Space } from 'antd';
import { UserOutlined, EditOutlined, LockOutlined, SaveOutlined, CloseOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentApi } from '@/services/studentApi';
import {
  buildFullName,
  getGenderLabel,
  getStudentStatusProps,
  getBranchLabel,
  formatDate,
} from '@/utils/formatters';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './StudentPage.module.scss';

const { Title, Text } = Typography;

export default function StudentProfilePage() {
  const queryClient = useQueryClient();
  const [changePwdModal, setChangePwdModal] = useState(false);
  const [changePwdForm] = Form.useForm();

  const { data: user, isLoading } = useQuery({
    queryKey: ['student', 'profile'],
    queryFn: studentApi.getProfile,
    staleTime: 5 * 60 * 1000,
  });

  const changePwdMutation = useMutation({
    mutationFn: studentApi.changePassword,
    onSuccess: () => {
      message.success('Đổi mật khẩu thành công!');
      setChangePwdModal(false);
      changePwdForm.resetFields();
    },
    onError: (error) => {
      const msg = getApiErrorMessage(error, 'Đổi mật khẩu thất bại. Vui lòng thử lại.');
      message.error(msg);
    },
  });

  const handleChangePwd = (values) => {
    changePwdMutation.mutate({
      oldPassword: values.old_password,
      newPassword: values.new_password,
      confirmPassword: values.confirm_password,
    });
  };

  if (isLoading) {
    return (
      <div className={styles.page}>
        <Card className={styles.infoCard}>
          <Skeleton active avatar paragraph={{ rows: 6 }} />
        </Card>
      </div>
    );
  }

  if (!user) return null;

  const statusProps = getStudentStatusProps(user.TrangThai);
  console.log(user);  
  return (
    <div className={styles.page}>
      <Card
        title={
          <Space>
            <UserOutlined style={{ color: '#1677ff' }} />
            Thông tin cá nhân
          </Space>
        }
        extra={
          <Space>
            <Button icon={<LockOutlined />} onClick={() => setChangePwdModal(true)}>
              Đổi mật khẩu
            </Button>
          </Space>
        }
        className={styles.infoCard}
      >
        <Row gutter={[32, 0]}>
          <Col xs={24} md={8}>
            <div className={styles.profileAvatar}>
              <div className={styles.avatarCircle}>
                <span className={styles.avatarInitial}>
                  {buildFullName(user.Ho, user.Ten)?.charAt(0)?.toUpperCase() || 'S'}
                </span>
              </div>
              <Title level={4} style={{ marginTop: 12, marginBottom: 4 }}>
                {buildFullName(user.Ho, user.Ten)}
              </Title>
              <Text type="secondary">{user.MaSV || user.userId}</Text>
              <div style={{ marginTop: 8 }}>
                <Tag color={statusProps.color}>{statusProps.label}</Tag>
              </div>
            </div>
          </Col>

          <Col xs={24} md={16}>
            <Descriptions column={{ xs: 1, sm: 2 }} bordered size="middle">
              <Descriptions.Item label="Mã sinh viên" span={2}>
                <Text strong>{user.MaSV || '—'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Họ">
                {user.Ho || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Tên">
                {user.Ten || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Email">
                {user.email || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Số điện thoại">
                {user.SDT || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Ngày sinh">
                {formatDate(user.NgaySinh)}
              </Descriptions.Item>
              <Descriptions.Item label="Giới tính">
                {getGenderLabel(user.GioiTinh)}
              </Descriptions.Item>
              <Descriptions.Item label="Địa chỉ" span={2}>
                {user.DiaChi || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Cơ sở">
                {getBranchLabel(user.MaCoSo)}
              </Descriptions.Item>
              <Descriptions.Item label="Khoa">
                {user.MaKhoa || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Trạng thái sinh viên">
                <Tag color={statusProps.color}>{statusProps.label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Ngày nhập học">
                {formatDate(user.NgayNhapHoc)}
              </Descriptions.Item>
              <Descriptions.Item label="User ID" span={2}>
                <Text type="secondary">{user.userId}</Text>
              </Descriptions.Item>
            </Descriptions>
          </Col>
        </Row>
      </Card>

      {/* Change Password Modal */}
      <Modal
        title={
          <Space>
            <LockOutlined style={{ color: '#1677ff' }} />
            Đổi mật khẩu
          </Space>
        }
        open={changePwdModal}
        onCancel={() => { setChangePwdModal(false); changePwdForm.resetFields(); }}
        footer={null}
        width={420}
        destroyOnClose
      >
        <Form
          form={changePwdForm}
          layout="vertical"
          onFinish={handleChangePwd}
          size="large"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="old_password"
            label="Mật khẩu hiện tại"
            rules={[{ required: true, message: 'Vui lòng nhập mật khẩu hiện tại' }]}
          >
            <Input.Password placeholder="Nhập mật khẩu hiện tại" />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="Mật khẩu mới"
            rules={[
              { required: true, message: 'Vui lòng nhập mật khẩu mới' },
              { min: 6, message: 'Mật khẩu phải có ít nhất 6 ký tự' },
            ]}
          >
            <Input.Password placeholder="Nhập mật khẩu mới" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="Xác nhận mật khẩu mới"
            dependencies={['new_password']}
            rules={[
              { required: true, message: 'Vui lòng xác nhận mật khẩu' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Mật khẩu xác nhận không khớp'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="Nhập lại mật khẩu mới" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => { setChangePwdModal(false); changePwdForm.resetFields(); }}>
                Hủy
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={changePwdMutation.isPending}
                icon={<SaveOutlined />}
              >
                Lưu mật khẩu
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
