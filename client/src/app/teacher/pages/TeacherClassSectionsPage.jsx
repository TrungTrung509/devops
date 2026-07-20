/**
 * Teacher Class Sections Page - View and manage teaching sections
 * Shows class sections assigned to the teacher
 */

import { Card, Table, Typography, Space, Tag, Empty, Skeleton, Button, Drawer, Descriptions, Popover } from 'antd';
import {
  BookOutlined,
  TeamOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { teacherClassSectionApi } from '@/services/teacherApi';
import { semesterApi } from '@/services/semesterApi';
import {
  getClassSectionStatusProps,
  getStudyFormLabel,
  getEnrollmentStatusProps,
  getDayOfWeekLabel,
  formatTimeSlot,
  formatDate,
  getBranchLabel,
  getWeekdayLabel,
  getWeekdayColor,
  formatLessonTime,
  buildSchedulePopoverItem,
} from '@/utils/formatters';
import styles from './TeacherPage.module.scss';

const { Title, Text } = Typography;

export default function TeacherClassSectionsPage() {
  const [drawer, setDrawer] = useState({ open: false, MaLopHP: null });
  const [drawerTab, setDrawerTab] = useState('info');

  const { data: mySectionsResp, isLoading, refetch } = useQuery({
    queryKey: ['teacher', 'my-sections'],
    queryFn: teacherClassSectionApi.getMyTeaching,
    staleTime: 2 * 60 * 1000,
  });

  const mySections = Array.isArray(mySectionsResp)
    ? mySectionsResp
    : (mySectionsResp?.items || []);

  const { data: semestersResp } = useQuery({
    queryKey: ['meta', 'semesters'],
    queryFn: semesterApi.getAll,
    staleTime: 30 * 60 * 1000,
  });

  const semesters = Array.isArray(semestersResp)
    ? semestersResp
    : (semestersResp?.items || []);

  const { data: sectionDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['teacher', 'section-detail', drawer.MaLopHP],
    queryFn: () => teacherClassSectionApi.getDetail(drawer.MaLopHP),
    staleTime: 2 * 60 * 1000,
    enabled: !!drawer.MaLopHP,
  });

  const { data: schedulesResp } = useQuery({
    queryKey: ['teacher', 'section-schedules', drawer.MaLopHP],
    queryFn: () => teacherClassSectionApi.getSchedules(drawer.MaLopHP),
    staleTime: 2 * 60 * 1000,
    enabled: !!drawer.MaLopHP && drawerTab === 'schedule',
  });

  const schedules = Array.isArray(schedulesResp) ? schedulesResp : [];

  const { data: enrollmentsResp } = useQuery({
    queryKey: ['teacher', 'section-enrollments', drawer.MaLopHP],
    queryFn: () => teacherClassSectionApi.getEnrollments(drawer.MaLopHP),
    staleTime: 2 * 60 * 1000,
    enabled: !!drawer.MaLopHP && drawerTab === 'students',
  });

  const enrollments = Array.isArray(enrollmentsResp) ? enrollmentsResp : [];

  const handleOpenDrawer = (MaLopHP) => {
    setDrawer({ open: true, MaLopHP });
    setDrawerTab('info');
  };

  const handleCloseDrawer = () => {
    setDrawer({ open: false, MaLopHP: null });
  };

  const columns = [
    {
      title: 'Mã lớp HP',
      dataIndex: 'MaLopHP',
      key: 'MaLopHP',
      width: 140,
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
      width: 90,
      render: (v) => v || '—',
    },
    {
      title: 'Học kỳ',
      dataIndex: 'MaHocKy',
      key: 'MaHocKy',
      width: 100,
    },
    {
      title: 'Cơ sở',
      dataIndex: 'MaCoSo',
      key: 'MaCoSo',
      width: 130,
      render: (coso) => <Tag color="blue">{getBranchLabel(coso)}</Tag>,
    },
    {
      title: 'Sĩ số',
      key: 'SiSo',
      width: 110,
      align: 'center',
      render: (_, record) => (
        <Space size={4}>
          <TeamOutlined style={{ color: '#595959', fontSize: 12 }} />
          <Text>{record.SiSoHienTai ?? 0}/{record.SiSoToiDa ?? 0}</Text>
        </Space>
      ),
    },
    {
      title: 'Hình thức',
      dataIndex: 'HinhThucHoc',
      key: 'HinhThucHoc',
      width: 100,
      render: (form) => getStudyFormLabel(form),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThaiLop',
      key: 'TrangThaiLop',
      width: 90,
      align: 'center',
      render: (status) => {
        const props = getClassSectionStatusProps(status);
        return <Tag color={props.color}>{props.label}</Tag>;
      },
    },
    {
      title: 'Lịch học',
      key: 'lichHoc',
      width: 150,
      render: (_, record) => {
        const lichHoc = record.LichHoc || [];

        // Lop khong co lich
        if (lichHoc.length === 0) {
          return <Text type="secondary" style={{ fontSize: 12 }}>Chưa có lịch</Text>;
        }

        // Mot lich hoc -> hien thi truc tiep voi gio thuc
        if (lichHoc.length === 1) {
          const item = lichHoc[0];
          const thuLabel = getWeekdayLabel(item.ThuTrongTuan);
          const timeRange = formatLessonTime(item.TietBatDau, item.SoTiet);
          return (
            <Space direction="vertical" size={3} style={{ width: '100%' }}>
              <Space size={4}>
                <Tag color={getWeekdayColor(item.ThuTrongTuan)}>{thuLabel}</Tag>
              </Space>
              <Text style={{ fontSize: 12, color: '#1677ff', fontWeight: 500 }}>
                {timeRange}
              </Text>
              <Text type="secondary" style={{ fontSize: 11 }}>
                {item.TenPhong || item.MaPhong || '—'}
              </Text>
            </Space>
          );
        }

        // Nhieu lich hoc -> Popover
        const sorted = [...lichHoc].sort((a, b) => {
          if (a.ThuTrongTuan !== b.ThuTrongTuan) return a.ThuTrongTuan - b.ThuTrongTuan;
          return a.TietBatDau - b.TietBatDau;
        });

        const popoverContent = (
          <div style={{ minWidth: 280 }}>
            <Text strong style={{ display: 'block', marginBottom: 10, fontSize: 13, color: '#1d39c4' }}>
              {sorted.length} buoi hoc
            </Text>
            {sorted.map((item, idx) => {
              const { thuLabel, weekdayColor, timeRange, phong, ghiChu } = buildSchedulePopoverItem(item);
              return (
                <div
                  key={item.MaLich || idx}
                  style={{
                    padding: '8px 0',
                    borderBottom: idx < sorted.length - 1 ? '1px solid #f0f0f0' : 'none',
                  }}
                >
                  <Space direction="vertical" size={3}>
                    <Space size={4}>
                      <Tag color={weekdayColor}>{thuLabel}</Tag>
                      <Text style={{ fontSize: 12, color: '#1677ff', fontWeight: 500 }}>
                        {timeRange}
                      </Text>
                    </Space>
                    <Text style={{ fontSize: 12 }}>
                      <Text type="secondary">Phong: </Text>
                      {phong}
                    </Text>
                    <Text style={{ fontSize: 12 }}>
                      <Text type="secondary">Ngay: </Text>
                      {item.NgayBatDau && item.NgayKetThuc
                        ? `${formatDate(item.NgayBatDau)} — ${formatDate(item.NgayKetThuc)}`
                        : '—'}
                    </Text>
                    {ghiChu && (
                      <Text type="secondary" style={{ fontSize: 12, fontStyle: 'italic' }}>
                        {ghiChu}
                      </Text>
                    )}
                  </Space>
                </div>
              );
            })}
          </div>
        );

        return (
          <Popover
            content={popoverContent}
            title="Lich hoc cua lop"
            trigger="click"
            placement="left"
            overlayStyle={{ maxWidth: 340 }}
          >
            <Tag
              color="processing"
              style={{ cursor: 'pointer', userSelect: 'none' }}
            >
              {lichHoc.length} buoi hoc
            </Tag>
          </Popover>
        );
      },
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 100,
      align: 'center',
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          icon={<InfoCircleOutlined />}
          onClick={() => handleOpenDrawer(record.MaLopHP)}
        >
          Chi tiết
        </Button>
      ),
    },
  ];

  const scheduleColumns = [
    {
      title: 'Thứ',
      dataIndex: 'ThuTrongTuan',
      key: 'ThuTrongTuan',
      width: 100,
      render: (thu) => <Tag color={thu >= 7 ? 'orange' : 'blue'}>{getDayOfWeekLabel(thu)}</Tag>,
    },
    {
      title: 'Phòng',
      dataIndex: 'MaPhong',
      key: 'MaPhong',
      width: 100,
      render: (v) => v || '—',
    },
    {
      title: 'Tiết',
      key: 'tiet',
      width: 120,
      render: (_, record) => formatTimeSlot(record.TietBatDau, record.SoTiet),
    },
    {
      title: 'Ngày bắt đầu',
      dataIndex: 'NgayBatDau',
      key: 'NgayBatDau',
      width: 120,
      render: (date) => formatDate(date),
    },
    {
      title: 'Ngày kết thúc',
      dataIndex: 'NgayKetThuc',
      key: 'NgayKetThuc',
      width: 120,
      render: (date) => formatDate(date),
    },
  ];

  const enrollmentColumns = [
    {
      title: 'Mã SV',
      dataIndex: 'MaSV',
      key: 'MaSV',
      width: 120,
      render: (code) => <Text code style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: 'Họ tên',
      key: 'hoTen',
      render: (_, record) => record.HoTenSinhVien || record.MaSV || '—',
    },
    {
      title: 'Ngày đăng ký',
      dataIndex: 'NgayDangKy',
      key: 'NgayDangKy',
      width: 150,
      render: (date) => formatDate(date),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'TrangThaiDangKy',
      key: 'TrangThaiDangKy',
      width: 120,
      render: (status) => {
        const props = getEnrollmentStatusProps(status);
        return <Tag color={props.color}>{props.label}</Tag>;
      },
    },
    {
      title: 'Lần đăng ký',
      dataIndex: 'LanDangKy',
      key: 'LanDangKy',
      width: 100,
      align: 'center',
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <Title level={3} className={styles.pageTitle}>Lớp học phần phụ trách</Title>
          <Text type="secondary">
            Danh sách lớp học phần bạn được phân công giảng dạy.
          </Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
      </div>

      <Card
        title={
          <Space>
            <BookOutlined style={{ color: '#722ed1' }} />
            <span>Danh sách lớp học phần ({mySections.length})</span>
          </Space>
        }
        className={styles.tableCard}
      >
        {isLoading ? (
          <Skeleton active paragraph={{ rows: 6 }} />
        ) : mySections.length > 0 ? (
          <Table
            columns={columns}
            dataSource={mySections}
            rowKey="MaLopHP"
            pagination={{
              pageSize: 15,
              showSizeChanger: true,
              showTotal: (t, r) => `${r[0]}-${r[1]} trong ${t}`,
            }}
            scroll={{ x: 1280 }}
            size="middle"
          />
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Bạn chưa được phân công lớp học phần nào"
          />
        )}
      </Card>

      {/* Detail Drawer */}
      <Drawer
        title={
          <Space>
            <BookOutlined style={{ color: '#722ed1' }} />
            Chi tiết lớp học phần
          </Space>
        }
        placement="right"
        width={600}
        open={drawer.open}
        onClose={handleCloseDrawer}
        extra={
          <Text type="secondary">{drawer.MaLopHP}</Text>
        }
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button
              type={drawerTab === 'info' ? 'primary' : 'default'}
              size="small"
              onClick={() => setDrawerTab('info')}
            >
              Thông tin
            </Button>
            <Button
              type={drawerTab === 'schedule' ? 'primary' : 'default'}
              size="small"
              onClick={() => setDrawerTab('schedule')}
            >
              Lịch học
            </Button>
            <Button
              type={drawerTab === 'students' ? 'primary' : 'default'}
              size="small"
              onClick={() => setDrawerTab('students')}
            >
              Sinh viên ({sectionDetail?.DanhSachDangKy?.length || enrollments.length})
            </Button>
          </Space>
        </div>

        {detailLoading ? (
          <Skeleton active paragraph={{ rows: 6 }} />
        ) : sectionDetail ? (
          <>
            {drawerTab === 'info' && (
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="Mã lớp HP">{sectionDetail.MaLopHP}</Descriptions.Item>
                <Descriptions.Item label="Mã học phần">{sectionDetail.MaHocPhan}</Descriptions.Item>
                <Descriptions.Item label="Tên học phần">{sectionDetail.TenHocPhan || '—'}</Descriptions.Item>
                <Descriptions.Item label="Nhóm">{sectionDetail.TenLopHP || '—'}</Descriptions.Item>
                <Descriptions.Item label="Học kỳ">{sectionDetail.MaHocKy}</Descriptions.Item>
                <Descriptions.Item label="Cơ sở">{getBranchLabel(sectionDetail.MaCoSo)}</Descriptions.Item>
                <Descriptions.Item label="Giảng viên">{sectionDetail.TenGiangVien || sectionDetail.MaGV || '—'}</Descriptions.Item>
                <Descriptions.Item label="Sĩ số">
                  {sectionDetail.SiSoHienTai ?? 0} / {sectionDetail.SiSoToiDa ?? 0}
                </Descriptions.Item>
                <Descriptions.Item label="Hình thức">{getStudyFormLabel(sectionDetail.HinhThucHoc)}</Descriptions.Item>
                <Descriptions.Item label="Trạng thái">
                  {(() => {
                    const sp = getClassSectionStatusProps(sectionDetail.TrangThaiLop);
                    return <Tag color={sp.color}>{sp.label}</Tag>;
                  })()}
                </Descriptions.Item>
              </Descriptions>
            )}

            {drawerTab === 'schedule' && (
              <Table
                columns={scheduleColumns}
                dataSource={sectionDetail?.LichHoc || schedules}
                rowKey="MaLich"
                pagination={false}
                size="small"
                locale={{ emptyText: 'Chưa có lịch học' }}
              />
            )}

            {drawerTab === 'students' && (
              <Table
                columns={enrollmentColumns}
                dataSource={sectionDetail?.DanhSachDangKy || enrollments}
                rowKey="MaDangKy"
                pagination={{ pageSize: 10, showSizeChanger: true }}
                size="small"
                locale={{ emptyText: 'Chưa có sinh viên đăng ký' }}
              />
            )}
          </>
        ) : null}
      </Drawer>
    </div>
  );
}
