/**
 * Schedule utilities - normalize and transform schedule data for calendar view
 *
 * Data shape from backend (PascalCase):
 *   { MaLich, MaLopHP, MaPhong, ThuTrongTuan, TietBatDau, SoTiet,
 *     NgayBatDau, NgayKetThuc, GhiChu, TenPhong }
 *
 * ClassSection shape:
 *   { MaLopHP, MaHocPhan, TenHocPhan, TenLopHP, HinhThucHoc, ... }
 */

import { getDayOfWeekLabel } from '@/utils/formatters';

export const DAY_ORDER = [2, 3, 4, 5, 6, 7, 8];
export const SHORT_DAY_LABELS = {
  2: 'T2',
  3: 'T3',
  4: 'T4',
  5: 'T5',
  6: 'T6',
  7: 'T7',
  8: 'CN',
};

/**
 * Determine the max slot number used across all schedules.
 * Used to set grid row count.
 */
export function getMaxSlot(schedules = []) {
  if (!schedules.length) return 12;
  return schedules.reduce((max, s) => {
    const end = (s.TietBatDau || 1) + (s.SoTiet || 1) - 1;
    return end > max ? end : max;
  }, 12);
}

/**
 * Build a 2D matrix for calendar grid rendering.
 * Returns: { slots: number[], grid: { [thu]: { [slot]: ScheduleItem[] } } }
 *
 * Each slot covers one period (Tiết 1, Tiết 2, ...).
 * A schedule with TietBatDau=3, SoTiet=2 occupies slots 3 and 4.
 */
export function buildCalendarMatrix(schedules = [], maxSlot = 12) {
  const slots = [];
  for (let i = 1; i <= maxSlot; i++) {
    slots.push(i);
  }

  const grid = {};
  DAY_ORDER.forEach((thu) => {
    grid[thu] = {};
    slots.forEach((slot) => {
      grid[thu][slot] = [];
    });
  });

  schedules.forEach((schedule) => {
    const thu = schedule.ThuTrongTuan;
    if (!DAY_ORDER.includes(thu)) return;

    const start = schedule.TietBatDau || 1;
    const count = schedule.SoTiet || 1;
    for (let i = 0; i < count; i++) {
      const slot = start + i;
      if (slot <= maxSlot) {
        grid[thu][slot].push(schedule);
      }
    }
  });

  return { slots, grid };
}

/**
 * Enrich a schedule item with class section info for display.
 * Returns a new object (non-mutating).
 */
export function enrichScheduleWithClassSection(schedule, classSectionMap) {
  const cs = classSectionMap[schedule.MaLopHP];
  return {
    ...schedule,
    TenHocPhan: cs?.TenHocPhan || schedule.TenHocPhan,
    TenLopHP: cs?.TenLopHP || schedule.TenLopHP,
    MaHocPhan: cs?.MaHocPhan || schedule.MaHocPhan,
    HinhThucHoc: cs?.HinhThucHoc || schedule.HinhThucHoc,
  };
}

/**
 * Get display color based on study form.
 * Returns CSS color string.
 */
export function getScheduleBlockColor(hinhThucHoc, index = 0) {
  const colors = [
    '#e6f4ff', // blue-1  - Online
    '#f6ffed', // green-1 - Offline
    '#fff1f0', // red-1   - Hybrid
    '#fff7e6', // orange-1
    '#f9f0ff', // purple-1
    '#e6fffb', // cyan-1
  ];
  if (hinhThucHoc === 'Online') return colors[0];
  if (hinhThucHoc === 'Hybrid') return colors[2];
  return colors[index % colors.length];
}

export function getScheduleBlockBorder(hinhThucHoc, index = 0) {
  const borders = [
    '#1677ff',
    '#52c41a',
    '#ff4d4f',
    '#fa8c16',
    '#722ed1',
    '#13c2c2',
  ];
  if (hinhThucHoc === 'Online') return borders[0];
  if (hinhThucHoc === 'Hybrid') return borders[2];
  return borders[index % borders.length];
}
