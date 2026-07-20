/**
 * Teacher Profile Page - View and update teacher profile
 */

import { useState } from 'react';
import { Card, Row, Col, Typography, Descriptions, Tag, Button, Skeleton, Form, Input, message, Modal, Space } from 'antd';
import { UserOutlined, LockOutlined, SaveOutlined } from '@ant-design/icons';
import { useQuery, useMutation } from '@tanstack/react-query';
import { teacherApi } from '@/services/teacherApi';
import {
  buildFullName,
  getGenderLabel,
  getTeacherStatusProps,
  getBranchLabel,
  getDegreeLabel,
  getRankLabel,
  formatDate,
} from '@/utils/formatters';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './TeacherPage.module.scss';

const { Title, Text } = Typography;

export default function TeacherProfilePage() {
  const [changePwdModal, setChangePwdModal] = useState(false);
  const [changePwdForm] = Form.useForm();

  const { data: user, isLoading } = useQuery({
    queryKey: ['teacher', 'profile'],
    queryFn: teacherApi.getProfile,
    staleTime: 5 * 60 * 1000,
  });

  const changePwdMutation = useMutation({
    mutationFn: teacherApi.changePassword,
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

  const statusProps = getTeacherStatusProps(user.TrangThai);

  return (
    <div className={styles.page}>
      <Card
        title={
          <Space>
            <UserOutlined style={{ color: '#722ed1' }} />
            Thông tin cá nhân
          </Space>
        }
        extra={
          <Button icon={<LockOutlined />} onClick={() => setChangePwdModal(true)}>
            Đổi mật khẩu
          </Button>
        }
        className={styles.infoCard}
      >
        <Row gutter={[32, 0]}>
          <Col xs={24} md={8}>
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'linear-gradient(135deg, #722ed1, #531d93)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
                <span style={{ fontSize: 32, fontWeight: 700, color: '#fff' }}>
                  {buildFullName(user.Ho, user.Ten)?.charAt(0)?.toUpperCase() || 'G'}
                </span>
              </div>
              <Title level={4} style={{ marginBottom: 4 }}>{buildFullName(user.Ho, user.Ten)}</Title>
              <Text type="secondary">{user.MaGV || user.UserId || user.userId}</Text>
              <div style={{ marginTop: 8 }}>
                <Tag color={statusProps.color}>{statusProps.label}</Tag>
              </div>
            </div>
          </Col>

          <Col xs={24} md={16}>
            <Descriptions column={{ xs: 1, sm: 2 }} bordered size="middle">
              <Descriptions.Item label="Mã giảng viên" span={2}>
                <Text strong>{user.MaGV || '—'}</Text>
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
              <Descriptions.Item label="Học vị">
                {getDegreeLabel(user.HocVi)}
              </Descriptions.Item>
              <Descriptions.Item label="Học hàm">
                {getRankLabel(user.HocHam)}
              </Descriptions.Item>
              <Descriptions.Item label="Cơ sở">
                {getBranchLabel(user.MaCoSo)}
              </Descriptions.Item>
              <Descriptions.Item label="Khoa">
                {user.MaKhoa || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Trạng thái">
                <Tag color={statusProps.color}>{statusProps.label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Ngày vào làm">
                {formatDate(user.NgayVaoLam)}
              </Descriptions.Item>
              <Descriptions.Item label="User ID" span={2}>
                <Text type="secondary">{user.UserId || user.userId}</Text>
              </Descriptions.Item>
            </Descriptions>
          </Col>
        </Row>
      </Card>

      {/* Change Password Modal */}
      <Modal
        title={<Space><LockOutlined style={{ color: '#722ed1' }} />Đổi mật khẩu</Space>}
        open={changePwdModal}
        onCancel={() => { setChangePwdModal(false); changePwdForm.resetFields(); }}
        footer={null}
        width={420}
        destroyOnClose
      >
        <Form form={changePwdForm} layout="vertical" onFinish={handleChangePwd} size="large" style={{ marginTop: 16 }}>
          <Form.Item name="old_password" label="Mật khẩu hiện tại" rules={[{ required: true, message: 'Vui lòng nhập mật khẩu hiện tại' }]}>
            <Input.Password placeholder="Nhập mật khẩu hiện tại" />
          </Form.Item>
          <Form.Item name="new_password" label="Mật khẩu mới" rules={[{ required: true, message: 'Vui lòng nhập mật khẩu mới' }, { min: 6, message: 'Ít nhất 6 ký tự' }]}>
            <Input.Password placeholder="Nhập mật khẩu mới" />
          </Form.Item>
          <Form.Item name="confirm_password" label="Xác nhận mật khẩu mới" dependencies={['new_password']} rules={[
            { required: true, message: 'Vui lòng xác nhận mật khẩu' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) return Promise.resolve();
                return Promise.reject(new Error('Mật khẩu xác nhận không khớp'));
              },
            }),
          ]}>
            <Input.Password placeholder="Nhập lại mật khẩu mới" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => { setChangePwdModal(false); changePwdForm.resetFields(); }}>Hủy</Button>
              <Button type="primary" htmlType="submit" loading={changePwdMutation.isPending} icon={<SaveOutlined />}>
                Lưu mật khẩu
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
