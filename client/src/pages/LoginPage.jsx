/**
 * LoginPage - Authentication page
 */

import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, Alert, Checkbox } from 'antd';
import { UserOutlined, LockOutlined, BookOutlined } from '@ant-design/icons';
import { useLoginMutation } from '@/hooks/useAuth';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './LoginPage.module.scss';

const { Title, Text, Link } = Typography;

export default function LoginPage() {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const loginMutation = useLoginMutation({
    onSuccess: (data) => {
      // Login success -> token already saved by useLoginMutation.
      // Role was decoded from JWT and stored by useLoginMutation.
      // Navigation to admin or dashboard is handled inside useLoginMutation.
    },
    onError: () => {
      // Error is shown via loginMutation.isError in the form.
    },
  });

  return (
    <div className={styles.page}>
      <div className={styles.background} />

      <div className={styles.container}>
        {/* Left Panel - Branding */}
        <div className={styles.brandPanel}>
          <div className={styles.brandContent}>
            <div className={styles.brandLogo}>
              <BookOutlined style={{ fontSize: 48, color: '#fff' }} />
            </div>
            <Title className={styles.brandTitle}>Hệ thống Đăng ký Tín chỉ</Title>
            <Text className={styles.brandSubtitle}>
              Quản lý đăng ký học phần trực tuyến<br />
              Phân tán theo cơ sở đào tạo
            </Text>

            <div className={styles.brandFeatures}>
              <div className={styles.featureItem}>
                <div className={styles.featureDot} />
                <Text className={styles.featureText}>Đăng ký lớp học phần theo cơ sở</Text>
              </div>
              <div className={styles.featureItem}>
                <div className={styles.featureDot} />
                <Text className={styles.featureText}>Quản lý thời khóa biểu tự động</Text>
              </div>
              <div className={styles.featureItem}>
                <div className={styles.featureDot} />
                <Text className={styles.featureText}>Theo dõi lịch sử đăng ký</Text>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Login Form */}
        <div className={styles.formPanel}>
          <Card className={styles.formCard} bordered={false}>
            <div className={styles.formHeader}>
              <div className={styles.formLogo}>
                <BookOutlined style={{ fontSize: 28, color: '#1677ff' }} />
              </div>
              <Title level={3} className={styles.formTitle}>Đăng nhập</Title>
              <Text type="secondary" className={styles.formSubtitle}>
                Vui lòng nhập thông tin tài khoản để tiếp tục
              </Text>
            </div>

            {loginMutation.isError && (
              <Alert
                type="error"
                message={getApiErrorMessage(loginMutation.error, 'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.')}
                showIcon
                className={styles.alert}
              />
            )}

            <Form
              form={form}
              layout="vertical"
              onFinish={(values) => loginMutation.mutate({ username: values.username, password: values.password })}
              requiredMark={false}
              size="large"
              initialValues={{ remember: true }}
            >
              <Form.Item
                name="username"
                label="Tên đăng nhập"
                rules={[
                  { required: true, message: 'Vui lòng nhập tên đăng nhập' },
                  { min: 3, message: 'Tên đăng nhập phải có ít nhất 3 ký tự' },
                ]}
              >
                <Input
                  prefix={<UserOutlined style={{ color: '#bfbfbf' }} />}
                  placeholder="Nhập tên đăng nhập"
                  autoComplete="username"
                  maxLength={50}
                />
              </Form.Item>

              <Form.Item
                name="password"
                label="Mật khẩu"
                rules={[
                  { required: true, message: 'Vui lòng nhập mật khẩu' },
                  { min: 6, message: 'Mật khẩu phải có ít nhất 6 ký tự' },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
                  placeholder="Nhập mật khẩu"
                  autoComplete="current-password"
                />
              </Form.Item>

              <Form.Item>
                <div className={styles.formOptions}>
                  <Form.Item name="remember" valuePropName="checked" noStyle>
                    <Checkbox>Ghi nhớ đăng nhập</Checkbox>
                  </Form.Item>
                  <Link href="#" disabled>Quên mật khẩu?</Link>
                </div>
              </Form.Item>

              <Form.Item style={{ marginBottom: 0 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  block
                  loading={loginMutation.isPending}
                  size="large"
                >
                  {loginMutation.isPending ? 'Đang đăng nhập...' : 'Đăng nhập'}
                </Button>
              </Form.Item>
            </Form>

            <div className={styles.demoHint}>
              <Text type="secondary" className={styles.demoText}>
                Tài khoản demo: <strong>admin</strong> / <strong>admin123</strong>
              </Text>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
