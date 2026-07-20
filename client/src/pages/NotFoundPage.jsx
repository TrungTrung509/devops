/**
 * NotFoundPage - 404 page
 */

import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { HomeOutlined } from '@ant-design/icons';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f0f2f5',
    }}>
      <Result
        status="404"
        title="404"
        subTitle="Trang bạn đang tìm kiếm không tồn tại hoặc đã bị di chuyển."
        extra={
          <Button
            type="primary"
            icon={<HomeOutlined />}
            onClick={() => navigate('/dashboard', { replace: true })}
          >
            Về trang chủ
          </Button>
        }
      />
    </div>
  );
}
