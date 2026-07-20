/**
 * Teacher Schedule Page - View teaching schedule
 * Shows schedule based on teacher's assigned class sections.
 * Fetches ONLY the teacher's own sections — no fetching all schedules.
 */

import { useState } from 'react';
import { Card, Table, Typography, Space, Tag, Empty, Button, Row, Col, Segmented } from 'antd';
import {
  CalendarOutlined,
  BarsOutlined,
  ClockCircleOutlined,
  HomeOutlined,
  BookOutlined,
  ReloadOutlined,
  BankOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { teacherClassSectionApi } from '@/services/teacherApi';
import ScheduleCalendarView from '@/components/ScheduleCalendarView';
import {
  getDayOfWeekLabel,
  formatTimeSlot,
  formatDate,
} from '@/utils/formatters';
import styles from './TeacherPage.module.scss';

const { Title, Text } = Typography;

const THU_ORDER = [2, 3, 4, 5, 6, 7, 8];

export default function TeacherSchedulePage() {
  const [viewMode, setViewMode] = useState('list');

  // Fetch my teaching sections — each section contains nested LichHoc[]
  const { data: sectionsResp, isLoading, isError, refetch } = useQuery({
    queryKey: ['teacher', 'my-sections'],
    queryFn: teacherClassSectionApi.getMyTeaching,
    staleTime: 2 * 60 * 1000,
  });

  // Flatten LichHoc from each section into row-per-schedule entries
  const sections = Array.isArray(sectionsResp) ? sectionsResp : (sectionsResp?.items || []);
  const scheduleRows = sections.flatMap((sec) =>
    (sec.LichHoc || []).map((sch) => ({
      ...sch,
      MaLopHP: sec.MaLopHP,
      TenLopHP: sec.TenLopHP,
      MaHP: sec.MaHocPhan || sec.MaHP,
      TenHP: sec.TenHocPhan,
      SoTinChi: sec.SoTinChi,
      MaHocKy: sec.MaHocKy,
      MaCoSo: sec.MaCoSo,
      TenCoSo: sec.TenCoSo,
      MaGV: sec.MaGV,
      TenGiangVien: sec.TenGiangVien,
      HinhThucHoc: sec.HinhThucHoc,
      key: `${sec.MaLopHP}-${sch.MaLich}`,
    }))
  );

  // Build classSectionMap for calendar enrichment
  const classSectionMap = {};
  sections.forEach((sec) => {
    classSectionMap[sec.MaLopHP] = {
      MaLopHP: sec.MaLopHP,
      MaHocPhan: sec.MaHocPhan || sec.MaHP,
      TenHocPhan: sec.TenHocPhan,
      TenLopHP: sec.TenLopHP,
      MaCoSo: sec.MaCoSo,
      TenCoSo: sec.TenCoSo,
      MaGV: sec.MaGV,
      TenGiangVien: sec.TenGiangVien,
      HinhThucHoc: sec.HinhThucHoc,
    };
  });

  const sortedSchedules = [...scheduleRows].sort(
    (a, b) =>
      (a.ThuTrongTuan || 0) - (b.ThuTrongTuan || 0) ||
      (a.TietBatDau || 0) - (b.TietBatDau || 0)
  );

  const scheduleColumns = [
    {
      title: 'Thứ',
      dataIndex: 'ThuTrongTuan',
      key: 'ThuTrongTuan',
      width: 100,
      render: (thu) => {
        const label = getDayOfWeekLabel(thu);
        return (
          <Tag color={thu >= 7 ? 'orange' : 'blue'} style={{ minWidth: 80, textAlign: 'center' }}>
            {label}
          </Tag>
        );
      },
      sorter: (a, b) => (a.ThuTrongTuan || 0) - (b.ThuTrongTuan || 0),
    },
    {
      title: 'Mã lớp HP',
      dataIndex: 'MaLopHP',
      key: 'MaLopHP',
      width: 140,
      render: (code) => <Text code style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: 'Tên học phần',
      dataIndex: 'TenHP',
      key: 'TenHP',
      ellipsis: true,
      render: (v) => v || '—',
    },
    {
      title: 'Nhóm',
      dataIndex: 'TenLopHP',
      key: 'TenLopHP',
      width: 80,
      render: (v) => v || '—',
    },
    {
      title: 'Cơ sở',
      dataIndex: 'TenCoSo',
      key: 'TenCoSo',
      width: 130,
      render: (v, record) => (
        <Space size={4}>
          <BankOutlined style={{ color: '#595959', fontSize: 12 }} />
          <Text>{v || record.MaCoSo}</Text>
        </Space>
      ),
    },
    {
      title: 'Phòng',
      dataIndex: 'TenPhong',
      key: 'TenPhong',
      width: 110,
      render: (v, record) => (
        <Space size={4}>
          <HomeOutlined style={{ color: '#595959', fontSize: 12 }} />
          <Text>{v || record.MaPhong || '—'}</Text>
          {record.ToaNha && (
            <Text type="secondary" style={{ fontSize: 11 }}>
              ({record.ToaNha})
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Tiết',
      key: 'tiet',
      width: 100,
      render: (_, record) => (
        <Space size={4}>
          <ClockCircleOutlined style={{ color: '#595959', fontSize: 12 }} />
          <Text>{formatTimeSlot(record.TietBatDau, record.SoTiet)}</Text>
        </Space>
      ),
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

  const isEmpty = !isLoading && sortedSchedules.length === 0;

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <Title level={3} className={styles.pageTitle}>Lịch dạy</Title>
          <Text type="secondary">
            Lịch giảng dạy dựa trên các lớp học phần bạn phụ trách.
          </Text>
        </div>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            Làm mới
          </Button>
        </Space>
      </div>

      {/* View Toggle */}
      <div className={styles.viewToggle}>
        <Segmented
          value={viewMode}
          onChange={setViewMode}
          options={[
            {
              label: (
                <Space size={4}>
                  <BarsOutlined />
                  <span>Danh sách</span>
                </Space>
              ),
              value: 'list',
            },
            {
              label: (
                <Space size={4}>
                  <CalendarOutlined />
                  <span>Thời khóa biểu</span>
                </Space>
              ),
              value: 'calendar',
            },
          ]}
        />
      </div>

      {/* Summary stats */}
      {!isLoading && !isEmpty && (
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          {[
            { label: 'Lớp phụ trách', value: sections.length, color: '#722ed1' },
            { label: 'Tổng buổi dạy', value: sortedSchedules.length, color: '#52c41a' },
          ].map((stat, i) => (
            <Col xs={12} md={6} key={i}>
              <Card size="small" bodyStyle={{ padding: '12px 16px' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>{stat.label}</Text>
                <Text strong style={{ fontSize: 24, color: stat.color, display: 'block' }}>
                  {stat.value}
                </Text>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* ── LIST VIEW ─────────────────────────────────────── */}
      {viewMode === 'list' && (
        <>
          <Card
            title={
              <Space>
                <CalendarOutlined style={{ color: '#722ed1' }} />
                Lịch dạy cá nhân
                {!isLoading && !isEmpty && (
                  <Tag color="purple">{sortedSchedules.length} buổi dạy</Tag>
                )}
              </Space>
            }
          >
            {isError ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={<Text type="danger">Không thể tải lịch dạy. Vui lòng thử lại.</Text>}
              />
            ) : !isLoading && isEmpty ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <span>
                    Chưa có lịch dạy. Bạn chưa được phân công lớp học phần nào.
                  </span>
                }
              />
            ) : (
              <Table
                columns={scheduleColumns}
                dataSource={sortedSchedules}
                rowKey="key"
                loading={isLoading}
                pagination={{
                  pageSize: 15,
                  showSizeChanger: true,
                  showTotal: (total, range) => `${range[0]}-${range[1]} trong ${total}`,
                }}
                scroll={{ x: 900 }}
                size="middle"
              />
            )}
          </Card>

          {/* Per-day breakdown */}
          {!isLoading && !isEmpty && (
            <Card
              title={
                <Space>
                  <BookOutlined style={{ color: '#722ed1' }} />
                  Thống kê theo thứ
                </Space>
              }
              style={{ marginTop: 16 }}
            >
              <Row gutter={[12, 12]}>
                {THU_ORDER.map((thu) => {
                  const count = sortedSchedules.filter((s) => s.ThuTrongTuan === thu).length;
                  return (
                    <Col xs={12} sm={8} md={6} lg={3} key={thu}>
                      <Card size="small" bodyStyle={{ padding: '12px' }}>
                        <Space direction="vertical" size={4} style={{ width: '100%' }}>
                          <Text type="secondary">{getDayOfWeekLabel(thu)}</Text>
                          <Text strong style={{ fontSize: 24, color: count > 0 ? '#722ed1' : '#bfbfbf' }}>
                            {count}
                          </Text>
                          <Text type="secondary" style={{ fontSize: 12 }}>buổi dạy</Text>
                        </Space>
                      </Card>
                    </Col>
                  );
                })}
              </Row>
            </Card>
          )}
        </>
      )}

      {/* ── CALENDAR VIEW ─────────────────────────────────── */}
      {viewMode === 'calendar' && (
        <ScheduleCalendarView
          schedules={sortedSchedules}
          classSectionMap={classSectionMap}
          role="teacher"
          isLoading={isLoading}
        />
      )}
    </div>
  );
}
