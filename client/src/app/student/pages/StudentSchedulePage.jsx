/**
 * Student Schedule Page - View personal class schedule
 * Fetches ONLY enrolled class sections + schedules for the current student.
 * Supports three view modes: list, calendar grid, and course summary.
 */

import { useState } from 'react';
import { Card, Table, Typography, Space, Tag, Empty, Button, Row, Col, Segmented, Divider } from 'antd';
import {
  CalendarOutlined,
  BarsOutlined,
  ClockCircleOutlined,
  HomeOutlined,
  BookOutlined,
  ReloadOutlined,
  BankOutlined,
  TeamOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { studentEnrollmentApi } from '@/services/studentApi';
import ScheduleCalendarView from '@/components/ScheduleCalendarView';
import CourseScheduleSummary from '@/components/CourseScheduleSummary';
import {
  getDayOfWeekLabel,
  formatTimeSlot,
  formatDate,
} from '@/utils/formatters';
import styles from './StudentPage.module.scss';

const { Title, Text } = Typography;

const THU_ORDER = [2, 3, 4, 5, 6, 7, 8];

export default function StudentSchedulePage() {
  const [viewMode, setViewMode] = useState('list');
  const [maHocKy, setMaHocKy] = useState(undefined);

  const { data: timetableItems = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['student', 'timetable', maHocKy],
    queryFn: () => studentEnrollmentApi.getTimetable(maHocKy ? { maHocKy } : {}),
    staleTime: 30 * 1000,
  });

  // ── Flatten schedules for list view ──────────────────────────────
  const scheduleRows = timetableItems.flatMap((item) =>
    (item.LichHoc || []).map((sch) => ({
      ...sch,
      MaLopHP: item.MaLopHP,
      TenLopHP: item.TenLopHP,
      MaHP: item.MaHP,
      TenHP: item.TenHP,
      SoTinChi: item.SoTinChi,
      MaHocKy: item.MaHocKy,
      MaCoSo: item.MaCoSo,
      TenCoSo: item.TenCoSo,
      MaGV: item.MaGV,
      TenGiangVien: item.TenGiangVien,
      TrangThaiDangKy: item.TrangThaiDangKy,
      // Study form — passed through for color coding in calendar
      HinhThucHoc: item.HinhThucHoc,
      key: `${item.MaLopHP}-${sch.MaLich}`,
    }))
  );

  const sortedRows = [...scheduleRows].sort(
    (a, b) =>
      (a.ThuTrongTuan || 0) - (b.ThuTrongTuan || 0) ||
      (a.TietBatDau || 0) - (b.TietBatDau || 0)
  );

  // ── Build classSectionMap for calendar view ──────────────────────
  // scheduleRows already contain all class-section fields (MaHP, TenHP,
  // TenLopHP, MaCoSo, TenCoSo, MaGV, TenGiangVien, HinhThucHoc),
  // so we build a map MaLopHP -> enrichment object.
  const classSectionMap = {};
  timetableItems.forEach((item) => {
    classSectionMap[item.MaLopHP] = {
      MaLopHP: item.MaLopHP,
      MaHocPhan: item.MaHP,
      TenHocPhan: item.TenHP,
      TenLopHP: item.TenLopHP,
      MaCoSo: item.MaCoSo,
      TenCoSo: item.TenCoSo,
      MaGV: item.MaGV,
      TenGiangVien: item.TenGiangVien,
      HinhThucHoc: item.HinhThucHoc,
    };
  });

  // Sort timetable items by course name
  const sortedTimetableItems = [...timetableItems].sort((a, b) =>
    (a.TenHP || '').localeCompare(b.TenHP || '')
  );

  // ── Table columns ────────────────────────────────────────────────
  const scheduleColumns = [
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
      render: (v, record) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ fontSize: 14 }}>{v || '—'}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>Mã HP: {record.MaHP} • {record.SoTinChi} tín chỉ</Text>
        </Space>
      ),
    },
    {
      title: 'Nhóm',
      dataIndex: 'TenLopHP',
      key: 'TenLopHP',
      width: 100,
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
      title: 'Giảng viên',
      dataIndex: 'TenGiangVien',
      key: 'TenGiangVien',
      width: 150,
      ellipsis: true,
      render: (v) => v || '—',
    },
    {
      title: 'Lịch học chi tiết',
      dataIndex: 'LichHoc',
      key: 'LichHoc',
      render: (lichHoc) => {
        if (!lichHoc || !lichHoc.length) {
          return <Text type="secondary">—</Text>;
        }
        // Sắp xếp lịch học theo thứ tự thứ trong tuần để hiển thị trực quan
        const sortedLich = [...lichHoc].sort((a, b) => (a.ThuTrongTuan || 0) - (b.ThuTrongTuan || 0));
        return (
          <Space direction="vertical" size={8} style={{ width: '100%', padding: '4px 0' }}>
            {sortedLich.map((sch, index) => {
              const thuLabel = getDayOfWeekLabel(sch.ThuTrongTuan);
              const isWeekend = sch.ThuTrongTuan >= 7;
              return (
                <div
                  key={sch.MaLich || index}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    padding: '6px 12px',
                    backgroundColor: '#fafafa',
                    borderRadius: '6px',
                    border: '1px solid #f0f0f0',
                    borderLeft: '3px solid #1677ff',
                  }}
                >
                  <Space size={12} wrap>
                    <Tag color={isWeekend ? 'orange' : 'blue'} style={{ minWidth: 65, textAlign: 'center', margin: 0 }}>
                      {thuLabel}
                    </Tag>
                    <Text strong style={{ fontSize: 13 }}>
                      <ClockCircleOutlined style={{ marginRight: 4, color: '#8c8c8c' }} />
                      {formatTimeSlot(sch.TietBatDau, sch.SoTiet)}
                    </Text>
                    <Text style={{ fontSize: 13 }}>
                      <HomeOutlined style={{ marginRight: 4, color: '#8c8c8c' }} />
                      {sch.TenPhong || sch.MaPhong || '—'}
                      {sch.ToaNha && <Text type="secondary" style={{ fontSize: 12 }}> ({sch.ToaNha})</Text>}
                    </Text>
                  </Space>
                  <div style={{ fontSize: 11, color: '#8c8c8c', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <CalendarOutlined style={{ fontSize: 11 }} />
                    <span>Thời gian: {formatDate(sch.NgayBatDau)} - {formatDate(sch.NgayKetThuc)}</span>
                  </div>
                </div>
              );
            })}
          </Space>
        );
      },
    },
  ];

  // ── Summary stats ────────────────────────────────────────────────
  const totalTinChi = timetableItems.reduce(
    (s, item) => s + (item.SoTinChi || 0), 0
  );

  const isEmpty = !isLoading && sortedRows.length === 0;

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <Title level={3} className={styles.pageTitle}>Lịch học</Title>
          <Text type="secondary">
            Lịch học cá nhân dựa trên các lớp học phần đã đăng ký.
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

      {/* Controls & Stats inline row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px', backgroundColor: '#fff', padding: '8px 12px', borderRadius: '8px', border: '1px solid #f0f0f0' }}>
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
            {
              label: (
                <Space size={4}>
                  <UnorderedListOutlined />
                  <span>Theo học phần</span>
                </Space>
              ),
              value: 'course',
            },
          ]}
        />

        {!isLoading && !isEmpty && (
          <Space size={16} align="center" style={{ flexWrap: 'wrap' }}>
            <Space size={6}>
              <BookOutlined style={{ color: '#1677ff' }} />
              <Text type="secondary" style={{ fontSize: '13px' }}>Lớp:</Text>
              <Text strong style={{ color: '#1677ff', fontSize: '14px' }}>{timetableItems.length}</Text>
            </Space>
            <Divider type="vertical" style={{ margin: 0 }} />
            <Space size={6}>
              <CalendarOutlined style={{ color: '#52c41a' }} />
              <Text type="secondary" style={{ fontSize: '13px' }}>Buổi học:</Text>
              <Text strong style={{ color: '#52c41a', fontSize: '14px' }}>{sortedRows.length}</Text>
            </Space>
            <Divider type="vertical" style={{ margin: 0 }} />
            <Space size={6}>
              <TeamOutlined style={{ color: '#fa8c16' }} />
              <Text type="secondary" style={{ fontSize: '13px' }}>Tín chỉ:</Text>
              <Text strong style={{ color: '#fa8c16', fontSize: '14px' }}>{totalTinChi}</Text>
            </Space>
          </Space>
        )}
      </div>

      {/* ── LIST VIEW ─────────────────────────────────────── */}
      {viewMode === 'list' && (
        <>
          <Card
            title={
              <Space>
                <CalendarOutlined style={{ color: '#1677ff' }} />
                Lịch học cá nhân
                {!isLoading && !isEmpty && (
                  <Tag color="blue">{sortedRows.length} buổi học</Tag>
                )}
              </Space>
            }
          >
            {isError ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={<Text type="danger">Không thể tải lịch học. Vui lòng thử lại.</Text>}
              />
            ) : !isLoading && isEmpty ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <span>
                    Chưa có lịch học.{' '}
                    <a href="/student/class-sections">Đăng ký lớp học phần</a> để xem lịch.
                  </span>
                }
              />
            ) : (
              <Table
                columns={scheduleColumns}
                dataSource={sortedTimetableItems}
                rowKey="MaLopHP"
                loading={isLoading}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total, range) => `${range[0]}-${range[1]} trong ${total}`,
                }}
                scroll={{ x: 1100 }}
                size="middle"
              />
            )}
          </Card>

          {/* Per-day breakdown */}
          {!isLoading && !isEmpty && (
            <Card
              title={
                <Space>
                  <BookOutlined style={{ color: '#1677ff' }} />
                  Thống kê theo thứ
                </Space>
              }
              style={{ marginTop: 16 }}
            >
              <Row gutter={[12, 12]}>
                {THU_ORDER.map((thu) => {
                  const count = sortedRows.filter((s) => s.ThuTrongTuan === thu).length;
                  return (
                    <Col xs={12} sm={8} md={6} lg={3} key={thu}>
                      <Card size="small" bodyStyle={{ padding: '12px' }}>
                        <Space direction="vertical" size={4} style={{ width: '100%' }}>
                          <Text type="secondary">{getDayOfWeekLabel(thu)}</Text>
                          <Text strong style={{ fontSize: 24, color: count > 0 ? '#1677ff' : '#bfbfbf' }}>
                            {count}
                          </Text>
                          <Text type="secondary" style={{ fontSize: 12 }}>buổi học</Text>
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
          schedules={sortedRows}
          classSectionMap={classSectionMap}
          role="student"
          isLoading={isLoading}
        />
      )}

      {/* ── COURSE SUMMARY VIEW ──────────────────────────────── */}
      {viewMode === 'course' && (
        <>
          {isError ? (
            <Card>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={<Text type="danger">Không thể tải lịch học. Vui lòng thử lại.</Text>}
              />
            </Card>
          ) : (
            <CourseScheduleSummary
              items={timetableItems}
              isLoading={isLoading}
            />
          )}
        </>
      )}
    </div>
  );
}
