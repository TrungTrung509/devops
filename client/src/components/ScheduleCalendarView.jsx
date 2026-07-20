/**
 * ScheduleCalendarView - Reusable calendar/timetable grid for schedule display.
 *
 * Props:
 *   schedules       - Array of ScheduleResponse (already flattened from timetable API)
 *   classSectionMap - Map of MaLopHP -> classSection for enriching display
 *   role            - 'student' | 'teacher' (controls which fields to show)
 *   isLoading       - boolean
 *   lichHocIndexMap - optional: { [MaLich]: index } to determine period order
 */

import { useMemo, useState } from 'react';
import { Card, Empty, Skeleton, Tooltip, Tag, Select, Button, Space } from 'antd';
import {
  CalendarOutlined,
  HomeOutlined,
  BookOutlined,
  LeftOutlined,
  RightOutlined,
  ClockCircleOutlined,
  UserOutlined,
} from '@ant-design/icons';
import {
  DAY_ORDER,
  SHORT_DAY_LABELS,
  buildCalendarMatrix,
  enrichScheduleWithClassSection,
  getScheduleBlockColor,
  getScheduleBlockBorder,
} from '@/utils/scheduleUtils';
import {
  getDayOfWeekLabel,
  formatTimeSlot,
  formatDateRange,
  formatPeriodLabel,
  getPeriodBadgeColor,
  formatDate,
  formatLessonTime,
} from '@/utils/formatters';
import styles from './ScheduleCalendar.module.scss';

const TIET_LABEL = 'Tiết';

const LESSON_TIMES = {
  1: '07:00-07:50',
  2: '08:00-08:50',
  3: '09:00-09:50',
  4: '10:00-10:50',
  5: '11:00-11:50',
  6: '13:00-13:50',
  7: '14:00-14:50',
  8: '15:00-15:50',
  9: '16:00-16:50',
  10: '17:00-17:50',
  11: '18:00-18:50',
  12: '19:00-19:50',
};

// Utility: Parse date string (YYYY-MM-DD or DD/MM/YYYY) to Date object safely
function parseDate(dateStr) {
  if (!dateStr) return new Date();
  if (dateStr instanceof Date) {
    return isNaN(dateStr.getTime()) ? new Date() : dateStr;
  }
  
  const str = String(dateStr).trim();
  
  // Try parsing DD/MM/YYYY format
  if (str.includes('/')) {
    const parts = str.split(' ')[0].split('/');
    if (parts.length === 3) {
      const d = Number(parts[0]);
      const m = Number(parts[1]);
      const y = Number(parts[2]);
      if (!isNaN(d) && !isNaN(m) && !isNaN(y)) {
        return new Date(y, m - 1, d);
      }
    }
  }

  // Fallback to standard JS Date parsing
  const parsed = new Date(str);
  if (!isNaN(parsed.getTime())) {
    return parsed;
  }

  // If still invalid, try extracting YYYY-MM-DD
  const match = str.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    const y = Number(match[1]);
    const m = Number(match[2]);
    const d = Number(match[3]);
    return new Date(y, m - 1, d);
  }

  return new Date();
}

// Utility: Format Date object to DD/MM/YYYY
function formatLocalDate(date) {
  const d = String(date.getDate()).padStart(2, '0');
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const y = date.getFullYear();
  return `${d}/${m}/${y}`;
}

// Utility: Format Date to DD/MM
function formatDateShort(date) {
  const d = String(date.getDate()).padStart(2, '0');
  const m = String(date.getMonth() + 1).padStart(2, '0');
  return `${d}/${m}`;
}

// Utility: Get the Monday of the week for a given Date
function getMonday(date) {
  const d = new Date(date);
  const day = d.getDay();
  // day: 0 (Sun), 1 (Mon), ..., 6 (Sat)
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(d.setDate(diff));
  monday.setHours(0, 0, 0, 0);
  return monday;
}

// Utility: Generate week intervals based on all schedules' start and end dates
function generateWeeks(schedules) {
  if (!schedules || schedules.length === 0) return [];
  
  let minDate = null;
  let maxDate = null;
  
  schedules.forEach(s => {
    if (s.NgayBatDau) {
      const d = parseDate(s.NgayBatDau);
      if (!isNaN(d.getTime())) {
        if (!minDate || d < minDate) minDate = d;
      }
    }
    if (s.NgayKetThuc) {
      const d = parseDate(s.NgayKetThuc);
      if (!isNaN(d.getTime())) {
        if (!maxDate || d > maxDate) maxDate = d;
      }
    }
  });
  
  if (!minDate) minDate = new Date();
  if (!maxDate) {
    maxDate = new Date(minDate);
    maxDate.setDate(maxDate.getDate() + 15 * 7); // Default 15 weeks
  }
  
  const monday = getMonday(minDate);
  const weeks = [];
  let currentMonday = new Date(monday);
  let weekNum = 1;
  
  while (currentMonday <= maxDate || weeks.length === 0) {
    const sunday = new Date(currentMonday);
    sunday.setDate(sunday.getDate() + 6);
    sunday.setHours(23, 59, 59, 999);
    
    weeks.push({
      number: weekNum,
      startDate: new Date(currentMonday),
      endDate: sunday,
      label: `Tuần ${weekNum} [từ ngày ${formatLocalDate(currentMonday)} đến ngày ${formatLocalDate(sunday)}]`
    });
    
    currentMonday.setDate(currentMonday.getDate() + 7);
    weekNum++;
  }
  
  return weeks;
}

/**
 * Build the full popover content for a schedule entry.
 */
function buildScheduleTooltip(enriched, schedule) {
  return (
    <div style={{ fontSize: 12, minWidth: 220 }}>
      <div style={{ marginBottom: 6 }}>
        <strong style={{ fontSize: 13 }}>{enriched.TenHocPhan || enriched.MaLopHP}</strong>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <div><strong>Mã LHP:</strong> {enriched.MaLopHP}</div>
        {enriched.TenLopHP && <div><strong>Nhóm:</strong> {enriched.TenLopHP}</div>}
        {enriched.TenGiangVien && <div><strong>GV:</strong> {enriched.TenGiangVien} ({enriched.MaGV})</div>}
        {enriched.TenCoSo && <div><strong>Cơ sở:</strong> {enriched.TenCoSo}</div>}
        <div style={{ margin: '3px 0', borderTop: '1px solid #eee' }} />
        <div><strong>Thứ:</strong> {getDayOfWeekLabel(schedule.ThuTrongTuan)}</div>
        <div><strong>Tiết:</strong> {formatTimeSlot(schedule.TietBatDau, schedule.SoTiet)}</div>
        <div><strong>Phòng:</strong> {schedule.TenPhong || schedule.MaPhong || '—'}{schedule.ToaNha ? `, ${schedule.ToaNha}` : ''}</div>
        <div><strong>Ngày:</strong> {formatDateRange(schedule.NgayBatDau, schedule.NgayKetThuc)}</div>
        {schedule.GhiChu && <div><strong>Ghi chú:</strong> {schedule.GhiChu}</div>}
      </div>
    </div>
  );
}

/**
 * ScheduleItemCard — renders a single schedule block inside a grid cell.
 * Shows: TenHP, TenLopHP, Phong, Tiet, PeriodBadge, date range.
 * Tooltip on hover shows full details.
 */
function ScheduleItemCard({ schedule, classSectionMap, role, blockIndex }) {
  const enriched = enrichScheduleWithClassSection(schedule, classSectionMap);
  const borderColor = getScheduleBlockBorder(enriched.HinhThucHoc, blockIndex);

  const tooltipContent = buildScheduleTooltip(enriched, schedule);

  return (
    <Tooltip
      title={tooltipContent}
      placement="topLeft"
      mouseEnterDelay={0.2}
      overlayStyle={{ maxWidth: 300 }}
    >
      <div
        className={styles.scheduleCard}
        style={{
          backgroundColor: '#fafafa',
          border: '1px solid #e8e8e8',
          borderLeft: `4px solid ${borderColor || '#1677ff'}`,
          padding: '8px 10px',
          borderRadius: '6px',
        }}
      >
        {/* Course name */}
        <div style={{ fontWeight: 'bold', fontSize: '12px', color: '#262626', marginBottom: '4px', lineHeight: 1.3 }}>
          {enriched.TenHocPhan || enriched.MaLopHP}
        </div>

        {/* Schedule details */}
        <div style={{ fontSize: '11px', color: '#595959', display: 'flex', flexDirection: 'column', gap: '3px' }}>
          {enriched.TenLopHP && (
            <div>
              <span style={{ color: '#8c8c8c' }}>Nhóm:</span> {enriched.TenLopHP}
            </div>
          )}
          <div>
            <span style={{ color: '#8c8c8c' }}>Phòng:</span> <span style={{ fontWeight: 500 }}>{schedule.TenPhong || schedule.MaPhong || '—'}</span>
            {schedule.ToaNha && <span style={{ color: '#8c8c8c' }}> ({schedule.ToaNha})</span>}
          </div>
          {enriched.TenGiangVien && (
            <div>
              <span style={{ color: '#8c8c8c' }}>GV:</span> {enriched.TenGiangVien}
            </div>
          )}
        </div>
      </div>
    </Tooltip>
  );
}

/**
 * CalendarCell — renders the content of one grid cell (day-column × slot-row).
 * When multiple schedules occupy the same cell they stack vertically.
 */
function CalendarCell({ schedules, classSectionMap, role, maxSlot, isEmpty = true }) {
  if (isEmpty || !schedules || schedules.length === 0) {
    return <div className={styles.cellEmpty} />;
  }

  return (
    <div className={styles.cellContent}>
      {schedules.map((schedule, idx) => (
        <ScheduleItemCard
          key={schedule.MaLich || `${schedule.MaLopHP}-${schedule.ThuTrongTuan}-${schedule.TietBatDau}-${idx}`}
          schedule={schedule}
          classSectionMap={classSectionMap}
          role={role}
          blockIndex={idx}
        />
      ))}
    </div>
  );
}

export default function ScheduleCalendarView({
  schedules = [],
  classSectionMap = {},
  role = 'student',
  isLoading = false,
}) {
  const weeks = useMemo(() => generateWeeks(schedules), [schedules]);

  const [selectedWeekIndex, setSelectedWeekIndex] = useState(0);
  const [prevWeeksKey, setPrevWeeksKey] = useState('');
  const weeksKey = weeks.map(w => w.label).join('|');

  // Reset selected week index if schedules/weeks change
  if (weeksKey !== prevWeeksKey) {
    setPrevWeeksKey(weeksKey);
    const today = new Date();
    const index = weeks.findIndex(w => today >= w.startDate && today <= w.endDate);
    setSelectedWeekIndex(index !== -1 ? index : 0);
  }

  const activeWeek = weeks[selectedWeekIndex];

  // Filter schedules that run during the selected week
  const activeSchedules = useMemo(() => {
    if (!activeWeek) return [];
    return schedules.filter(s => {
      if (!s.NgayBatDau || !s.NgayKetThuc) return true;
      const sStart = parseDate(s.NgayBatDau);
      const sEnd = parseDate(s.NgayKetThuc);
      sStart.setHours(0, 0, 0, 0);
      sEnd.setHours(23, 59, 59, 999);
      
      // Calculate the exact date of s.ThuTrongTuan (where 2 is Mon, 8 is Sun) in the selected week
      const dayOffset = (s.ThuTrongTuan || 2) - 2;
      const actualDayDate = new Date(activeWeek.startDate);
      actualDayDate.setDate(actualDayDate.getDate() + dayOffset);
      actualDayDate.setHours(0, 0, 0, 0);
      
      // Check if that specific weekday of the week is within the schedule range
      return actualDayDate >= sStart && actualDayDate <= sEnd;
    });
  }, [schedules, activeWeek]);

  const maxSlot = useMemo(() => {
    if (!activeSchedules.length) return 12;
    return activeSchedules.reduce((max, s) => {
      const end = (s.TietBatDau || 1) + (s.SoTiet || 1) - 1;
      return end > max ? end : max;
    }, 12);
  }, [activeSchedules]);

  const { slots, grid } = useMemo(
    () => buildCalendarMatrix(activeSchedules, maxSlot),
    [activeSchedules, maxSlot]
  );

  const hasData = schedules.length > 0;

  const handlePrevWeek = () => {
    if (selectedWeekIndex > 0) {
      setSelectedWeekIndex(selectedWeekIndex - 1);
    }
  };

  const handleNextWeek = () => {
    if (selectedWeekIndex < weeks.length - 1) {
      setSelectedWeekIndex(selectedWeekIndex + 1);
    }
  };

  if (isLoading) {
    return (
      <Card className={styles.calendarCard}>
        <Skeleton active paragraph={{ rows: 8 }} />
      </Card>
    );
  }

  return (
    <Card
      className={styles.calendarCard}
      bodyStyle={{ padding: 0 }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <CalendarOutlined style={{ color: '#1677ff' }} />
          <span>Thời khóa biểu tuần</span>
          {hasData && (
            <span style={{ fontWeight: 400, color: '#8c8c8c', fontSize: 12 }}>
              ({schedules.length} buổi học học kỳ)
            </span>
          )}
        </div>
      }
    >
      {hasData ? (
        <div className={styles.calendarWrapper}>
          {/* Week Selector Controls */}
          {weeks.length > 0 && activeWeek && (
            <div className={styles.weekSelectorRow}>
              <span style={{ fontWeight: 500, fontSize: '13px' }}>Chọn tuần học:</span>
              <Button
                size="middle"
                icon={<LeftOutlined />}
                onClick={handlePrevWeek}
                disabled={selectedWeekIndex === 0}
              />
              <Select
                size="middle"
                value={selectedWeekIndex}
                onChange={setSelectedWeekIndex}
                options={weeks.map((w, idx) => ({
                  value: idx,
                  label: w.label,
                }))}
                style={{ width: 380 }}
                popupMatchSelectWidth={false}
              />
              <Button
                size="middle"
                icon={<RightOutlined />}
                onClick={handleNextWeek}
                disabled={selectedWeekIndex === weeks.length - 1}
              />
              {activeSchedules.length > 0 ? (
                <Tag color="processing" style={{ marginLeft: 8 }}>
                  Tuần này có {activeSchedules.length} buổi học
                </Tag>
              ) : (
                <Tag color="warning" style={{ marginLeft: 8 }}>
                  Tuần này không có buổi học nào
                </Tag>
              )}
            </div>
          )}

          {/* Grid header */}
          <div className={styles.calendarHeader}>
            <div className={styles.headerCorner}>
              <CalendarOutlined /> Tiết
            </div>
            {DAY_ORDER.map((thu) => {
              // Calculate exact date for the header cell based on selected week
              let dateShortStr = '';
              if (activeWeek) {
                const dayOffset = thu - 2; // 2 is Mon -> offset 0
                const dayDate = new Date(activeWeek.startDate);
                dayDate.setDate(dayDate.getDate() + dayOffset);
                dateShortStr = formatDateShort(dayDate);
              }

              return (
                <div
                  key={thu}
                  className={`${styles.headerCell} ${thu >= 7 ? styles.headerWeekend : ''}`}
                >
                  <span className={styles.headerDayShort}>T{thu === 8 ? 'CN' : thu}</span>
                  <span className={styles.headerDayFull}>
                    {thu === 8 ? 'Chủ Nhật' : `Thứ ${thu}`} {dateShortStr && `(${dateShortStr})`}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Grid body */}
          <div className={styles.calendarBody}>
            {slots.map((slot) => {
              const isRowEmpty = DAY_ORDER.every(thu => !grid[thu] || !grid[thu][slot] || grid[thu][slot].length === 0);

              return (
                <div key={slot} className={`${styles.gridRow} ${isRowEmpty ? styles.gridRowEmpty : ''}`}>
                  <div className={styles.slotLabel}>
                    <div className={isRowEmpty ? styles.slotContainerEmpty : styles.slotContainer}>
                      <span className={styles.slotNumber}>{slot}</span>
                      <span className={styles.slotTime}>{LESSON_TIMES[slot] || ''}</span>
                    </div>
                  </div>
                  {DAY_ORDER.map((thu) => (
                    <div
                      key={`${thu}-${slot}`}
                      className={`${styles.gridCell} ${thu >= 7 ? styles.weekendCell : ''}`}
                    >
                      <CalendarCell
                        schedules={grid[thu][slot]}
                        classSectionMap={classSectionMap}
                        role={role}
                        maxSlot={maxSlot}
                        isEmpty={!grid[thu] || grid[thu][slot].length === 0}
                      />
                    </div>
                  ))}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className={styles.calendarLegend}>
            <span style={{ fontSize: 11, color: '#8c8c8c' }}>
              Hover vào block để xem chi tiết đầy đủ. Lịch hiển thị ở trên đã được lọc theo đúng tuần bạn đã chọn.
            </span>
          </div>
        </div>
      ) : (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="Không có lịch để hiển thị"
        />
      )}
    </Card>
  );
}
