/**
 * CourseScheduleSummary - Shows enrolled courses grouped by course section.
 * Each course card displays the course info and all its schedule entries
 * with clear period labels (Nửa kỳ đầu / Nửa kỳ sau / Giai đoạn N).
 *
 * Props:
 *   items     - Array of StudentTimetableItem from /enrollments/my-timetable
 *   isLoading - boolean
 */

import { useState } from 'react';
import {
  Card,
  Typography,
  Space,
  Tag,
  List,
  Collapse,
  Badge,
  Tooltip,
  Row,
  Col,
  Divider,
} from 'antd';
import {
  BookOutlined,
  TeamOutlined,
  BankOutlined,
  CalendarOutlined,
  HomeOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import {
  formatPeriodLabel,
  getPeriodBadgeColor,
  formatDateRange,
  formatLessonRange,
  getDayOfWeekLabel,
  getWeekdayColor,
} from '@/utils/formatters';
import styles from './CourseScheduleSummary.module.scss';

const { Title, Text } = Typography;
const { Panel } = Collapse;

/**
 * Renders a single schedule row inside a course card.
 * Shows: thứ, tiết, phòng, tòa, ngày, giai đoạn.
 */
function ScheduleEntryRow({ schedule, index }) {
  const periodLabel = formatPeriodLabel(schedule, index);
  const periodColor = getPeriodBadgeColor(index);
  const thuLabel = getDayOfWeekLabel(schedule.ThuTrongTuan);
  const weekdayColor = getWeekdayColor(schedule.ThuTrongTuan);
  const tietLabel = formatLessonRange(schedule.TietBatDau, schedule.SoTiet);
  const phong = schedule.TenPhong || schedule.MaPhong || '—';
  const toa = schedule.ToaNha ? `, ${schedule.ToaNha}` : '';
  const dateRange = formatDateRange(schedule.NgayBatDau, schedule.NgayKetThuc);

  return (
    <div className={styles.scheduleEntry}>
      {/* Period badge */}
      <Tag
        color={periodColor}
        className={styles.periodBadge}
      >
        {periodLabel}
      </Tag>

      <div className={styles.scheduleEntryBody}>
        {/* Row 1: Thứ + Tiết */}
        <div className={styles.scheduleRow1}>
          <Tag color={weekdayColor} style={{ minWidth: 80, textAlign: 'center' }}>
            {thuLabel}
          </Tag>
          <Text strong style={{ fontSize: 13 }}>
            {tietLabel}
          </Text>
        </div>

        {/* Row 2: Phòng + Tòa */}
        <div className={styles.scheduleRow2}>
          <Space size={4}>
            <HomeOutlined style={{ color: '#595959', fontSize: 12 }} />
            <Text style={{ fontSize: 13 }}>{phong}</Text>
            {schedule.ToaNha && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {toa}
              </Text>
            )}
          </Space>
        </div>

        {/* Row 3: Date range */}
        <div className={styles.scheduleRow3}>
          <Space size={4}>
            <CalendarOutlined style={{ color: '#595959', fontSize: 12 }} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {dateRange}
            </Text>
          </Space>
        </div>
      </div>
    </div>
  );
}

/**
 * Renders a full course card with its schedule entries.
 */
function CourseCard({ item, schedules }) {
  const totalSchedules = schedules.length;
  const [expanded, setExpanded] = useState(
    totalSchedules <= 3 ? ['schedules'] : []
  );

  return (
    <Card
      size="small"
      className={styles.courseCard}
      title={
        <Space size={8}>
          <BookOutlined style={{ color: '#1677ff' }} />
          <Text strong style={{ fontSize: 14 }}>
            {item.TenHP || item.MaHP}
          </Text>
          {item.TrangThaiDangKy === 'DaDangKy' && (
            <Tag color="processing" style={{ marginLeft: 4 }}>
              Đã đăng ký
            </Tag>
          )}
        </Space>
      }
      extra={
        <Space size={4}>
          <Tag color="blue">{item.SoTinChi || '?'} tín chỉ</Tag>
          <Tag color="default">{totalSchedules} lịch</Tag>
        </Space>
      }
    >
      {/* Course metadata */}
      <Row gutter={[8, 4]} className={styles.courseMeta}>
        <Col span={24}>
          <Space size={12} wrap>
            <Space size={4}>
              <Text type="secondary" style={{ fontSize: 12 }}>Mã HP:</Text>
              <Text code style={{ fontSize: 11 }}>{item.MaHP}</Text>
            </Space>
            <Space size={4}>
              <Text type="secondary" style={{ fontSize: 12 }}>Lớp:</Text>
              <Text code style={{ fontSize: 11 }}>{item.MaLopHP}</Text>
            </Space>
            {item.TenLopHP && (
              <Space size={4}>
                <Text type="secondary" style={{ fontSize: 12 }}>Nhóm:</Text>
                <Text style={{ fontSize: 12 }}>{item.TenLopHP}</Text>
              </Space>
            )}
          </Space>
        </Col>
        <Col span={24}>
          <Space size={12} wrap>
            {item.TenGiangVien && (
              <Space size={4}>
                <TeamOutlined style={{ color: '#595959', fontSize: 12 }} />
                <Text style={{ fontSize: 12 }}>{item.TenGiangVien}</Text>
              </Space>
            )}
            {item.TenCoSo && (
              <Space size={4}>
                <BankOutlined style={{ color: '#595959', fontSize: 12 }} />
                <Text style={{ fontSize: 12 }}>{item.TenCoSo}</Text>
              </Space>
            )}
            {item.MaHocKy && (
              <Space size={4}>
                <CalendarOutlined style={{ color: '#595959', fontSize: 12 }} />
                <Text style={{ fontSize: 12 }}>{item.MaHocKy}</Text>
              </Space>
            )}
          </Space>
        </Col>
      </Row>

      <Divider style={{ margin: '8px 0' }} />

      {/* Schedule entries */}
      <div className={styles.scheduleList}>
        {schedules.map((sch, idx) => (
          <ScheduleEntryRow
            key={sch.MaLich || `${item.MaLopHP}-${idx}`}
            schedule={sch}
            index={idx}
          />
        ))}
      </div>
    </Card>
  );
}

/**
 * CourseScheduleSummary — top-level component
 *
 * Props:
 *   items     - StudentTimetableItem[] from the timetable API
 *   isLoading - boolean
 */
export default function CourseScheduleSummary({ items = [], isLoading = false }) {
  if (!items.length && !isLoading) {
    return null;
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <Title level={5} style={{ margin: 0 }}>
          <BookOutlined style={{ marginRight: 8, color: '#1677ff' }} />
          Lịch học theo học phần
        </Title>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {items.length} học phần đã đăng ký
        </Text>
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        <Space size={16} wrap>
          <Space size={4}>
            <Tag color="#52c41a">Nửa kỳ đầu</Tag>
            <Text type="secondary" style={{ fontSize: 11 }}>hoặc Giai đoạn 1</Text>
          </Space>
          <Space size={4}>
            <Tag color="#1677ff">Nửa kỳ sau</Tag>
            <Text type="secondary" style={{ fontSize: 11 }}>hoặc Giai đoạn 2+</Text>
          </Space>
        </Space>
        <Text type="secondary" style={{ fontSize: 11, fontStyle: 'italic' }}>
          Mỗi học phần có thể có nhiều lịch (nửa kỳ đầu / nửa kỳ sau khác nhau về phòng, tiết, ngày).
        </Text>
      </div>

      {/* Course cards */}
      <Row gutter={[12, 12]}>
        {items.map((item) => (
          <Col xs={24} md={12} lg={8} key={item.MaLopHP}>
            <CourseCard
              item={item}
              schedules={item.LichHoc || []}
            />
          </Col>
        ))}
      </Row>
    </div>
  );
}
