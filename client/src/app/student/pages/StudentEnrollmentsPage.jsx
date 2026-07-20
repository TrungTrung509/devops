/**
 * Student Enrollments History Page - View enrollment history and cancel
 */

import { Card, Table, Tag, Typography, Space, Button, Select, Popconfirm, message, Skeleton, Empty, Row, Col } from 'antd';
import {
  HistoryOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentEnrollmentApi } from '@/services/studentApi';
import { semesterApi } from '@/services/semesterApi';
import {
  getEnrollmentStatusProps,
  formatDateTime,
} from '@/utils/formatters';
import { getApiErrorMessage } from '@/utils/errorUtils';
import styles from './StudentPage.module.scss';

const { Title, Text } = Typography;

export default function StudentEnrollmentsPage() {
  const [selectedHocKy, setSelectedHocKy] = useState(null);
  const queryClient = useQueryClient();

  const { data: enrollmentsResp, isLoading, refetch } = useQuery({
    queryKey: ['student', 'enrollments', selectedHocKy],
    queryFn: () => studentEnrollmentApi.getHistory(selectedHocKy ? { MaHocKy: selectedHocKy } : {}),
    staleTime: 2 * 60 * 1000,
  });

  const enrollments = Array.isArray(enrollmentsResp) ? enrollmentsResp : [];

  const { data: semestersResp } = useQuery({
    queryKey: ['meta', 'semesters'],
    queryFn: semesterApi.getAll,
    staleTime: 30 * 60 * 1000,
  });

  const semesters = Array.isArray(semestersResp)
    ? semestersResp
    : (semestersResp?.items || []);

  const cancelMutation = useMutation({
    mutationFn: studentEnrollmentApi.cancel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student', 'enrollments'] });
      message.success('Hủy đăng ký thành công!');
    },
    onError: (error) => {
      const msg = getApiErrorMessage(error, 'Hủy đăng ký thất bại. Vui lòng thử lại.');
      message.error(msg);
    },
  });

  const handleCancel = async (record) => {
    await cancelMutation.mutateAsync(record.MaLopHP);
  };

  const columns = [
    {
      title: 'Mã lớp HP',
      dataIndex: 'MaLopHP',
      key: 'MaLopHP',
      width: 130,
      render: (code) => <Text code style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: 'Tên học phần',
      dataIndex: 'TenHocPhan',
      key: 'TenHocPhan',
      ellipsis: true,
    },
    {
      title: 'Nhóm',
      dataIndex: 'TenLopHP',
      key: 'TenLopHP',
      width: 100,
      render: (v) => v || '—',
    },
    {
      title: 'Học kỳ',
      dataIndex: 'MaHocKy',
      key: 'MaHocKy',
      width: 110,
    },
    {
      title: 'Ngày đăng ký',
      dataIndex: 'NgayDangKy',
      key: 'NgayDangKy',
      width: 150,
      render: (date) => formatDateTime(date),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThaiDangKy',
      key: 'TrangThaiDangKy',
      width: 130,
      align: 'center',
      render: (status) => {
        const props = getEnrollmentStatusProps(status);
        return <Tag color={props.color}>{props.label}</Tag>;
      },
    },
    {
      title: 'Ghi chú',
      dataIndex: 'GhiChu',
      key: 'GhiChu',
      ellipsis: true,
      render: (v) => v || '—',
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 120,
      align: 'center',
      render: (_, record) => {
        if (record.TrangThaiDangKy !== 'DaDangKy') return <Text type="secondary">—</Text>;
        return (
          <Popconfirm
            title="Xác nhận hủy đăng ký"
            description="Bạn có chắc muốn hủy đăng ký học phần này?"
            onConfirm={() => handleCancel(record)}
            okText="Hủy đăng ký"
            cancelText="Không"
            okButtonProps={{ danger: true, loading: cancelMutation.isPending }}
          >
            <Button danger size="small" icon={<CloseCircleOutlined />} loading={cancelMutation.isPending}>
              Hủy
            </Button>
          </Popconfirm>
        );
      },
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <Title level={3} className={styles.pageTitle}>Lịch sử đăng ký</Title>
          <Text type="secondary">
            Xem lịch sử đăng ký học phần. Chỉ có thể hủy các đăng ký đang ở trạng thái "Đã đăng ký".
          </Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
      </div>

      <Card className={styles.filterCard} bodyStyle={{ padding: '16px' }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Select
              placeholder="Lọc theo học kỳ"
              allowClear
              style={{ width: '100%' }}
              value={selectedHocKy}
              onChange={(val) => setSelectedHocKy(val)}
              size="middle"
            >
              {semesters.map((s) => (
                <Select.Option key={s.MaHocKy} value={s.MaHocKy}>
                  HK{s.KySo} – {s.NamHoc}
                </Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={16}>
            <Text type="secondary">
              Tổng cộng: <strong>{enrollments.length}</strong> đăng ký
              · <strong>{enrollments.filter((e) => e.TrangThaiDangKy === 'DaDangKy').length}</strong> đang đăng ký
              · <strong>{enrollments.filter((e) => e.TrangThaiDangKy === 'HoanThanh').length}</strong> hoàn thành
              · <strong>{enrollments.filter((e) => e.TrangThaiDangKy === 'DaHuy').length}</strong> đã hủy
            </Text>
          </Col>
        </Row>
      </Card>

      <Card className={styles.tableCard}>
        <Table
          columns={columns}
          dataSource={enrollments}
          rowKey="MaDangKy"
          loading={isLoading}
          pagination={{
            pageSize: 15,
            showSizeChanger: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} trong ${total}`,
            pageSizeOptions: ['15', '30', '50'],
          }}
          scroll={{ x: 900 }}
          size="middle"
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="Chưa có lịch sử đăng ký nào"
              />
            ),
          }}
        />
      </Card>
    </div>
  );
}
